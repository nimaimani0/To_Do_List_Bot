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
            status INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    

def add(user_id, task_text):
    pass

def get(user_id):
    pass

def edit_task_status(task_id, new_status):
    pass

def edit_task_text(task_id, new_text):
    pass

def delete(task_id):
    pass
