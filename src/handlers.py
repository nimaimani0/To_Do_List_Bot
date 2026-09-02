from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database
import keyboards

router = Router()

class Task(StatesGroup):
    wait_for_text = State()
    wait_for_edit = State()

@router.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id

    tasks = database.get(user_id)

    inline_keyboard = keyboards.main_keyboard(tasks)

    await message.answer("Hi and welcome to the bot.", reply_markup=inline_keyboard)


@router.callback_query(F.data == "add")
async def add_handler(callback: CallbackQuery, state: FSMContext):
    keyboard = keyboards.cancel_keyboard()
    await callback.message.edit_text("Please enter the task text:", reply_markup=keyboard)
    await state.set_state(Task.wait_for_text)
    await callback.answer()

@router.message(Task.wait_for_text, F.text, ~F.text.startswith("/"))
async def process_new_task(message: Message, state: FSMContext):
    user_id = message.from_user.id
    task_text = message.text

    try:
        database.add(user_id, task_text)
    except ValueError:
        await message.answer("Task Text cannot be empty.")
        return

    await state.clear()

    tasks = database.get(user_id)
    inline_keyboard = keyboards.main_keyboard(tasks)
    await message.answer("New Task added successfully.", reply_markup=inline_keyboard)


@router.callback_query(F.data.startswith("task:"))
async def task_menu_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    keyboard = keyboards.task_keyboard(task_id)
    await callback.message.edit_text("Please choose an option for this task:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("delete:"))
async def delete_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    deleted = database.delete(task_id, user_id)

    if not deleted:
        await callback.answer("Task not found.", show_alert=True)
        return

    tasks = database.get(user_id)
    keyboard = keyboards.main_keyboard(tasks)

    await callback.message.edit_text("Your task deleted. Updated Tasks:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "back")
async def back_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    tasks = database.get(user_id)
    keyboard = keyboards.main_keyboard(tasks)
    await callback.message.edit_text("Your tasks:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    tasks = database.get(user_id)

    keyboard = keyboards.main_keyboard(tasks)

    await callback.message.edit_text("Operation cancelled. Your tasks:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("done:"))
async def done_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    edited = database.edit_task_status(task_id, user_id, "done")

    if not edited:
        await callback.answer("Task not found.", show_alert=True)
        return

    tasks = database.get(user_id)
    keyboard = keyboards.main_keyboard(tasks)

    await callback.message.edit_text("Task marked as done. Updated Tasks:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:"))
async def edit_handler(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await state.update_data(task_id=task_id)
    await state.set_state(Task.wait_for_edit)

    keyboard = keyboards.cancel_keyboard()

    await callback.message.edit_text("Please write your new task text:", reply_markup=keyboard)
    await callback.answer()


@router.message(Task.wait_for_edit, F.text, ~F.text.startswith("/"))
async def process_edit_task(message: Message, state: FSMContext):
    user_id = message.from_user.id
    new_text = message.text
    data = await state.get_data()
    task_id = data.get("task_id")

    try:
        edited = database.edit_task_text(task_id, user_id, new_text)
        if not edited:
            await message.answer("Task not found.")
            return
    except ValueError:
        await message.answer("Task Text cannot be empty.")
        return

    await state.clear()
    tasks = database.get(user_id)
    keyboard = keyboards.main_keyboard(tasks)

    await message.answer("Task updated successfully. Your tasks:", reply_markup=keyboard)
