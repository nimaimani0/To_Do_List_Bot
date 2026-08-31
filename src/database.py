import sqlite3
Database="database.db"
def init():
    """
    create the todos table if it doesn't already exist.
    """

    conn = sqlite3.connect(Database)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT "pending"
        )
    """)

    conn.commit()
    conn.close()
    

def add(user_id, task_text):
    """add new todo"""
    task_text=task_text.strip()
    if not task_text:
        raise ValueError("task text cant be empty:/ ")
    with sqlite3.connect(Database)as conn:
        cursor=conn.execute("""user_id,task_text,status)VALUES(?,?,"pending")"""
                            ,(user_id,task_text))
        return cursor.lastrowid
    

def get(user_id):
    with sqlite3.connect(Database) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT
                id,
                user_id,
                task_text,
                status
            FROM todos
            WHERE user_id = ?
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    conn.close() 

def edit_task_status(task_id,user_id, new_status):
    if new_status not in ("pending", "done"):
        raise ValueError("Status must be pending or done.")

    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos
            SET status = ?
            WHERE id = ?
              AND user_id = ?
        """, (
            new_status,
            task_id,
            user_id
        ))

        return cursor.rowcount > 0
    

def edit_task_text(task_id,user_id, new_text):
    new_text = new_text.strip()
    if not new_text:
        raise ValueError("task text cannot be empty :/ .")

    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos
            SET task_text = ?
            WHERE id = ?
              AND user_id = ?
        """, (
            new_text,
            task_id,
            user_id
        ))

        return cursor.rowcount > 0

def delete(task_id,user_id):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            DELETE FROM todos
            WHERE id = ?
              AND user_id = ?
        """, (
            task_id,
            user_id
        ))

        return cursor.rowcount > 0
