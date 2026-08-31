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
            status INTEGER NOT NULL DEFAULT "pending"
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
    pass

def edit_task_status(task_id, new_status):
    pass

def edit_task_text(task_id, new_text):
    pass

def delete(task_id):
    pass
