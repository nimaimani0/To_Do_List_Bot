import jdatetime
from datetime import datetime
import pytz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_tehran_today():
    tehran_tz = pytz.timezone("Asia/Tehran")
    return jdatetime.date.fromgregorian(date=datetime.now(tehran_tz).date())

def is_past_date(date_str):
    today = get_tehran_today()
    y, m, d = map(int, date_str.split("-"))
    target_date = jdatetime.date(y, m, d)
    return target_date < today

def main_keyboard(tasks, selected_date):
    keyboard = []
    sorted_tasks = sorted(tasks, key=lambda x: x["status"] == "done")

    for task in sorted_tasks:
        text = task["task_text"]
        time_str = task["task_time"]
        priority = task.get("priority", "normal")

        if task["status"] == "done":
            strikethrough_text = "".join([char + chr(822) for char in text])
            display_text = f"✅ [{time_str}] {strikethrough_text}"
        else:
            p_emoji = "🔴" if priority == "high" else "🟢" if priority == "low" else "🟡"
            display_text = f"{p_emoji} [{time_str}] {text}"

        keyboard.append([
            InlineKeyboardButton(text=display_text, callback_data=f"task:{task['id']}:{selected_date}")
        ])

    if not is_past_date(selected_date):
        keyboard.append([
            InlineKeyboardButton(text="➕ Add New Task", callback_data=f"add:{selected_date}"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def task_keyboard(task_id, task_date, status="pending"):
    if is_past_date(task_date):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Reschedule", callback_data=f"edit_date:{task_id}:{task_date}")],
            [
                InlineKeyboardButton(text="✅ Done", callback_data=f"done:{task_id}:{task_date}"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_req:{task_id}:{task_date}")
            ],
            [InlineKeyboardButton(text="◀️ Back to Tasks", callback_data=f"day:{task_date}")]
        ])
    else:
        if status == "done":
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏪ Mark as Undone", callback_data=f"undone:{task_id}:{task_date}")],
                [InlineKeyboardButton(text="◀️ Back to Tasks", callback_data=f"day:{task_date}")]
            ])
        else:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔔 Reminders", callback_data=f"rem_menu:{task_id}:{task_date}")],
                [InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_menu:{task_id}:{task_date}")],
                [
                    InlineKeyboardButton(text="✅ Done", callback_data=f"done:{task_id}:{task_date}"),
                    InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_req:{task_id}:{task_date}")
                ],
                [InlineKeyboardButton(text="◀️ Back to Tasks", callback_data=f"day:{task_date}")]
            ])

def delete_confirm_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Yes, Delete Task", callback_data=f"confirm_delete:{task_id}:{task_date}"),
            InlineKeyboardButton(text="❌ No, Cancel", callback_data=f"task:{task_id}:{task_date}")
        ]
    ])


def after_add_keyboard(selected_date, task_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Add Reminder", callback_data=f"add_rem_menu:{task_id}:{selected_date}")],
        [InlineKeyboardButton(text="◀️ Back to Tasks", callback_data=f"day:{selected_date}")]
    ])

def reminders_management_keyboard(task_id, task_date, reminders):
    keyboard = []
    for rem in reminders:
        display = f"⏰ {rem['remind_date']} | {rem['remind_time']}"
        keyboard.append([
            InlineKeyboardButton(text=f"🗑 Delete: {display}", callback_data=f"del_rem_req:{rem['id']}:{task_id}:{task_date}")
        ])
    keyboard.append([InlineKeyboardButton(text="➕ Add Reminder", callback_data=f"add_rem_menu:{task_id}:{task_date}")])
    keyboard.append([InlineKeyboardButton(text="◀️ Back to Task", callback_data=f"task:{task_id}:{task_date}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def reminder_toggle_keyboard(task_id, task_date, selected_options=None):
    if selected_options is None:
        selected_options = []
    opts = {
        "5m": "5 Mins Before",
        "15m": "15 Mins Before",
        "30m": "30 Mins Before",
        "1h": "1 Hour Before",
        "1d": "1 Day Before"
    }
    keyboard = []
    for key, text in opts.items():
        marker = "✅ " if key in selected_options else ""
        keyboard.append([
            InlineKeyboardButton(text=f"{marker}{text}", callback_data=f"toggle_rem:{key}:{task_id}:{task_date}")
        ])

    keyboard.append([InlineKeyboardButton(text="⚙️ Custom Date/Time", callback_data=f"custom_rem:{task_id}:{task_date}")])
    keyboard.append([InlineKeyboardButton(text="💾 Save Reminders", callback_data=f"save_rems:{task_id}:{task_date}")])
    keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data=f"rem_menu:{task_id}:{task_date}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def delete_reminder_confirm_keyboard(reminder_id, task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Yes, Delete Reminder", callback_data=f"confirm_del_rem:{reminder_id}:{task_id}:{task_date}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"rem_menu:{task_id}:{task_date}")
        ]
    ])


def archive_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Copy to Today", callback_data=f"copy_today:{task_id}:{task_date}")],
        [InlineKeyboardButton(text="◀️ Back to Tasks", callback_data=f"day:{task_date}")]
    ])

def copy_time_prompt_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ Keep Same Time", callback_data=f"copy_same:{task_id}:{task_date}"),
            InlineKeyboardButton(text="⏱ Set New Time", callback_data=f"copy_new:{task_id}:{task_date}")
        ],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"task:{task_id}:{task_date}")]
    ])

def edit_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Edit Text", callback_data=f"edit_text:{task_id}:{task_date}")],
        [
            InlineKeyboardButton(text="📅 Edit Date", callback_data=f"edit_date:{task_id}:{task_date}"),
            InlineKeyboardButton(text="⏰ Edit Time", callback_data=f"edit_time:{task_id}:{task_date}")
        ],
        [InlineKeyboardButton(text="🏷 Edit Priority", callback_data=f"edit_prio_menu:{task_id}:{task_date}")],
        [InlineKeyboardButton(text="◀️ Back", callback_data=f"task:{task_id}:{task_date}")]
    ])

def edit_time_prompt_keyboard(task_id, new_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ Yes, Edit Time", callback_data=f"yes_edit_time:{task_id}:{new_date}"),
            InlineKeyboardButton(text="✅ No, Just Date", callback_data=f"no_edit_time:{task_id}:{new_date}")
        ],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ])

def get_days_in_jalali_month(year, month):
    if 1 <= month <= 6: return 31
    elif 7 <= month <= 11: return 30
    elif month == 12: return 30 if jdatetime.date.j_is_leap(year) else 29
    return 30

def calendar_keyboard(year, month, today, allow_past=True):
    rows = []
    prev_year = year
    prev_month = month - 1
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_year = year
    next_month = month + 1
    if next_month == 13:
        next_month = 1
        next_year += 1

    prev_allowed = allow_past or (prev_year, prev_month) >= (today.year, today.month)

    rows.append([
        InlineKeyboardButton(text="◀️" if prev_allowed else "·", callback_data=f"cal:{prev_year}:{prev_month}" if prev_allowed else "noop"),
        InlineKeyboardButton(text=f"{year}/{month:02d}", callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:{next_year}:{next_month}")
    ])

    rows.append([
        InlineKeyboardButton(text=x, callback_data="noop") for x in ["ش", "ی", "د", "س", "چ", "پ", "ج"]
    ])

    first_weekday = jdatetime.date(year, month, 1).weekday()
    days_in_month = get_days_in_jalali_month(year, month)
    day = 1
    week = []

    for _ in range(first_weekday):
        week.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    while day <= days_in_month:
        current = jdatetime.date(year, month, day)

        if not allow_past and current < today:
            week.append(InlineKeyboardButton(text="·", callback_data="noop"))
        else:
            marker = "🔵 " if current == today else ""
            date_str = f"{current.year:04d}-{current.month:02d}-{current.day:02d}"
            week.append(
                InlineKeyboardButton(
                    text=f"{marker}{day}",
                    callback_data=f"day:{date_str}"
                )
            )

        if len(week) == 7:
            rows.append(week)
            week = []
        day += 1

    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(text=" ", callback_data="noop"))
        rows.append(week)

    return InlineKeyboardMarkup(inline_keyboard=rows)

def calendar_for_date(selected_date):
    y, m, d = map(int, selected_date.split("-"))
    return calendar_keyboard(y, m, get_tehran_today())

def add_calendar_keyboard(selected_date):
    y, m, d = map(int, selected_date.split("-"))
    keyboard = calendar_keyboard(y, m, get_tehran_today()).inline_keyboard
    for row in keyboard:
        for button in row:
            if button.callback_data and button.callback_data.startswith("day:"):
                button.callback_data = button.callback_data.replace("day:", "add_date:", 1)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def edit_date_calendar_keyboard(selected_date, task_id):
    y, m, d = map(int, selected_date.split("-"))
    keyboard = calendar_keyboard(y, m, get_tehran_today(), allow_past=False).inline_keyboard
    for row in keyboard:
        for button in row:
            if button.callback_data and button.callback_data.startswith("day:"):
                chosen = button.callback_data.split(":", 1)[1]
                button.callback_data = f"edit_date_pick:{task_id}:{chosen}"
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def default_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗓 Calendar")]
        ],
        resize_keyboard=True,
    )

def time_picker_keyboard(hour: int, minute: int):
    h_str = f"{hour:02d}"
    m_str = f"{minute:02d}"

    keyboard = [
        [
            InlineKeyboardButton(text="+3h ⏫", callback_data=f"tp:h3u:{hour}:{minute}"),
            InlineKeyboardButton(text="+1h 🔼", callback_data=f"tp:h1u:{hour}:{minute}"),
            InlineKeyboardButton(text="+15m ⏫", callback_data=f"tp:m15u:{hour}:{minute}"),
            InlineKeyboardButton(text="+5m 🔼", callback_data=f"tp:m5u:{hour}:{minute}")
        ],
        [
            InlineKeyboardButton(text=f"{h_str}", callback_data="noop"),
            InlineKeyboardButton(text=":", callback_data="noop"),
            InlineKeyboardButton(text=f"{m_str}", callback_data="noop")
        ],
        [
            InlineKeyboardButton(text="-3h ⏬", callback_data=f"tp:h3d:{hour}:{minute}"),
            InlineKeyboardButton(text="-1h 🔽", callback_data=f"tp:h1d:{hour}:{minute}"),
            InlineKeyboardButton(text="-15m ⏬", callback_data=f"tp:m15d:{hour}:{minute}"),
            InlineKeyboardButton(text="-5m 🔽", callback_data=f"tp:m5d:{hour}:{minute}")
        ],
        [
            InlineKeyboardButton(text="🔄 AM/PM", callback_data=f"tp:flip:{hour}:{minute}")
        ],
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=f"tp:confirm:{hour}:{minute}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def reminder_notification_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Mark as Done", callback_data=f"rem_done:{task_id}:{task_date}")],
        [InlineKeyboardButton(text="⚙️ Manage Task", callback_data=f"rem_manage:{task_id}:{task_date}")],
        [InlineKeyboardButton(text="🧹 Got it!", callback_data="rem_got_it")]
    ])

def rem_date_calendar_keyboard(task_id, task_date):
    keyboard = calendar_keyboard(get_tehran_today().year, get_tehran_today().month, get_tehran_today(), allow_past=False).inline_keyboard
    for row in keyboard:
        for button in row:
            if button.callback_data and button.callback_data.startswith("day:"):
                chosen = button.callback_data.split(":", 1)[1]
                button.callback_data = f"rem_date_pick:{task_id}:{task_date}:{chosen}"
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def priority_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 High Priority", callback_data="new_prio:high")],
        [InlineKeyboardButton(text="🟡 Normal Priority", callback_data="new_prio:normal")],
        [InlineKeyboardButton(text="🟢 Low Priority", callback_data="new_prio:low")]
    ])

def edit_priority_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 High Priority", callback_data=f"set_prio:{task_id}:{task_date}:high")],
        [InlineKeyboardButton(text="🟡 Normal Priority", callback_data=f"set_prio:{task_id}:{task_date}:normal")],
        [InlineKeyboardButton(text="🟢 Low Priority", callback_data=f"set_prio:{task_id}:{task_date}:low")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"edit_menu:{task_id}:{task_date}")]
    ])
