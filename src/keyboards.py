from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard(tasks):
    keyboard = []

    for task in tasks:
        keyboard.append([
            InlineKeyboardButton(
                text=task["task_text"],
                callback_data=f"task:{task['id']}" )])

    keyboard.append([
        InlineKeyboardButton(
            text="🟢 Add",
            callback_data="add")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def task_keyboard(task_id):
    keyboard = [
        [
            InlineKeyboardButton(
                text="✏️ Edit",
                callback_data=f"edit:{task_id}"
                )
                ],
                [
            InlineKeyboardButton(
                text="🗑 Delete",
                callback_data=f"delete:{task_id}"
            )
            ],
        [
            InlineKeyboardButton(
                text="✅ Done",
                callback_data=f"done:{task_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Back",
                callback_data="back"
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)