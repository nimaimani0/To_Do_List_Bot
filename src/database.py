import sqlite3

Database = "database.db"

def init():
    conn = sqlite3.connect(Database)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT "pending",
            task_date TEXT NOT NULL,
            task_time TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT "normal"
        )
    """)

    try:
        cursor.execute("ALTER TABLE todos ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            remind_date TEXT NOT NULL,
            remind_time TEXT NOT NULL,
            FOREIGN KEY(task_id) REFERENCES todos(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def add(user_id, task_text, task_date, task_time, priority="normal"):
    task_text = task_text.strip()
    if not task_text:
        raise ValueError("Task text cannot be empty.")
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute(
            """INSERT INTO todos (user_id, task_text, status, task_date, task_time, priority) VALUES (?, ?, "pending", ?, ?, ?)""",
            (user_id, task_text, task_date, task_time, priority)
        )
        return cursor.lastrowid
def get(user_id, task_date):
    with sqlite3.connect(Database) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT id, user_id, task_text, status, task_date, task_time, priority
            FROM todos
            WHERE user_id = ? AND task_date = ? ORDER BY task_time ASC
        """, (user_id, task_date))
        return [dict(row) for row in cursor.fetchall()]



def edit_task_status(task_id, user_id, new_status):
    if new_status not in ("pending", "done"):
        raise ValueError("Status must be pending or done.")
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos SET status = ? WHERE id = ? AND user_id = ?
        """, (new_status, task_id, user_id))
        return cursor.rowcount > 0

def edit_task_text(task_id, user_id, new_text):
    new_text = new_text.strip()
    if not new_text:
        raise ValueError("Task text cannot be empty.")
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos SET task_text = ? WHERE id = ? AND user_id = ?
        """, (new_text, task_id, user_id))
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

def delete(task_id, user_id):
    with sqlite3.connect(Database) as conn:
        conn.execute("DELETE FROM reminders WHERE task_id = ? AND user_id = ?", (task_id, user_id))
        cursor = conn.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (task_id, user_id))
        return cursor.rowcount > 0

def check_overlap(user_id, task_date, task_time):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            SELECT id FROM todos
            WHERE user_id = ? AND task_date = ? AND task_time = ?
        """, (user_id, task_date, task_time))
        return cursor.fetchone() is not None


def add_reminder(task_id, user_id, remind_date, remind_time):
    with sqlite3.connect(Database) as conn:
        conn.execute("""
            INSERT INTO reminders (task_id, user_id, remind_date, remind_time)
            VALUES (?, ?, ?, ?)
        """, (task_id, user_id, remind_date, remind_time))

def get_reminders(task_id, user_id):
    with sqlite3.connect(Database) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT id, remind_date, remind_time FROM reminders
            WHERE task_id = ? AND user_id = ? ORDER BY remind_date, remind_time
        """, (task_id, user_id))
        return [dict(row) for row in cursor.fetchall()]

def delete_reminder(reminder_id, user_id):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            DELETE FROM reminders WHERE id = ? AND user_id = ?
        """, (reminder_id, user_id))
        return cursor.rowcount > 0

def get_due_reminders(current_date, current_time):
    with sqlite3.connect(Database) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT r.id as reminder_id, r.user_id, r.task_id, t.task_text, t.task_time, t.task_date
            FROM reminders r
            JOIN todos t ON r.task_id = t.id
            WHERE r.remind_date = ? AND r.remind_time = ? AND t.status = 'pending'
        """, (current_date, current_time))
        return [dict(row) for row in cursor.fetchall()]


def delete_all_reminders(task_id, user_id):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            DELETE FROM reminders WHERE task_id = ? AND user_id = ?
        """, (task_id, user_id))
        return cursor.rowcount > 0


def edit_task_priority(task_id, user_id, new_priority):
    with sqlite3.connect(Database) as conn:
        cursor = conn.execute("""
            UPDATE todos SET priority = ? WHERE id = ? AND user_id = ?
        """, (new_priority, task_id, user_id))
        return cursor.rowcount > 0
