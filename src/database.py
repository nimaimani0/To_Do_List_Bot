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
            status TEXT NOT NULL DEFAULT "pending",
            task_date TEXT NOT NULL,
            task_time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    

def add(user_id, task_text, task_date, task_time):
    """add new todo"""
    task_text=task_text.strip()
    if not task_text:
        raise ValueError("task text cant be empty:/ ")
    with sqlite3.connect(Database)as conn:
        cursor=conn.execute("""INSERT INTO todos (user_id,task_text,status,task_date, task_time) VALUES(?,?,"pending",?,?)"""
                            ,(user_id,task_text, task_date, task_time))
        return cursor.lastrowid
    

def get(user_id, task_date):
    with sqlite3.connect(Database) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT
                id,
                user_id,
                task_text,
                status,
                task_date,
                task_time
            FROM todos
            WHERE user_id = ? AND task_date = ? ORDER BY task_time ASC
        """, (user_id,task_date))
        return [dict(row) for row in cursor.fetchall()]

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

def edit_task_date(task_id, user_id, new_date):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos SET task_date = ? WHERE id = ? AND user_id = ?
        """, (new_date, task_id, user_id))
        return cursor.rowcount > 0


def edit_task_time(task_id, user_id, new_time):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos SET task_time = ? WHERE id = ? AND user_id = ?
        """, (new_time, task_id, user_id))
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


def check_overlap(user_id, task_date, task_time):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            SELECT id FROM todos
            WHERE user_id = ? AND task_date = ? AND task_time = ?
        """, (user_id, task_date, task_time))
        return cursor.fetchone() is not None

