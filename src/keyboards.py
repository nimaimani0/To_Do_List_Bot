from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard(tasks):
    keyboard = []
    sorted_tasks = sorted(tasks, key=lambda x: x["status"] == "done")

    for task in sorted_tasks:
        text = task["task_text"]

        if task["status"] == "done":
            strikethrough_text = "".join([char + chr(822) for char in text])
            text = f"✅ {strikethrough_text}"

        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"task:{task['id']}" )])

    keyboard.append([InlineKeyboardButton(text="🟢 Add", callback_data="add")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def task_keyboard(task_id):
    keyboard = [
        [InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit:{task_id}")],
        [InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete:{task_id}")],
        [InlineKeyboardButton(text="✅ Done", callback_data=f"done:{task_id}")],
        [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ])
