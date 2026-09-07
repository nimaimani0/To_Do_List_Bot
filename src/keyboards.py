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

        if task["status"] == "done":
            strikethrough_text = "".join([char + chr(822) for char in text])
            display_text = f"✅ [{time_str}] {strikethrough_text}"
        else:
            display_text = f"🕒 [{time_str}] {text}"

        keyboard.append([
            InlineKeyboardButton(
                text=display_text,
                callback_data=f"task:{task['id']}:{selected_date}"
            )
        ])

    if not is_past_date(selected_date):
        keyboard.append([
            InlineKeyboardButton(text="🟢 Add Task", callback_data=f"add:{selected_date}"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def task_keyboard(task_id, task_date, status="pending"):
    if is_past_date(task_date):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Reschedule", callback_data=f"edit_date:{task_id}:{task_date}")],
            [
                InlineKeyboardButton(text="✅ Done", callback_data=f"done:{task_id}:{task_date}"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete:{task_id}:{task_date}")
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
                [InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_menu:{task_id}:{task_date}")],
                [
                    InlineKeyboardButton(text="✅ Done", callback_data=f"done:{task_id}:{task_date}"),
                    InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete:{task_id}:{task_date}")
                ],
                [InlineKeyboardButton(text="◀️ Back to Tasks", callback_data=f"day:{task_date}")]
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


def delete_confirm_keyboard(task_id, task_date):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Yes, Delete", callback_data=f"confirm_delete:{task_id}:{task_date}"),
            InlineKeyboardButton(text="❌ No, Cancel", callback_data=f"task:{task_id}:{task_date}")
        ]
    ])
