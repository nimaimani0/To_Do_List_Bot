from datetime import datetime, timedelta
import jdatetime
import pytz
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

import database
import keyboards

router = Router()

class Task(StatesGroup):
    wait_for_text = State()
    wait_for_time = State()
    wait_for_priority = State()
    wait_for_edit_text = State()
    wait_for_edit_time = State()
    wait_for_rem_time = State()

def get_default_time():
    tehran_tz = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran_tz)
    rounded_minute = (now.minute // 5) * 5
    return now.hour, rounded_minute

def is_past_time(selected_date_str, selected_time_str):
    tehran_tz = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran_tz)
    tehran_today = jdatetime.date.fromgregorian(date=now.date()).isoformat()

    if selected_date_str == tehran_today:
        h, m = map(int, selected_time_str.split(':'))
        if h < now.hour or (h == now.hour and m < now.minute):
            return True
    return False

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    tehran_tz = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran_tz)
    today = jdatetime.date.fromgregorian(date=now.date())
    time_str = now.strftime("%H:%M")

    kb = keyboards.calendar_keyboard(today.year, today.month, today)
    reply_kb = keyboards.default_reply_keyboard()

    await message.answer(
        f"Hi and welcome to TICKO bot.\n📅 Date: {today.isoformat()}\n⏰ Time: {time_str}\n\n💡 Tip: You can always access your calendar by pressing the «🗓 Calendar» button below!\n\nPlease select a date:",
        reply_markup=reply_kb
    )
    await message.answer("🗓 Calendar:", reply_markup=kb)

@router.message(F.text == "🗓 Calendar")
async def planner_btn_handler(message: Message, state: FSMContext):
    await start_handler(message, state)

@router.callback_query(F.data == "back_to_calendar")
async def back_to_calendar_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    tehran_tz = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran_tz)
    today = jdatetime.date.fromgregorian(date=now.date())
    time_str = now.strftime("%H:%M")

    kb = keyboards.calendar_keyboard(today.year, today.month, today)
    await callback.message.edit_text(
        f"Hi and welcome to TICKO bot.\nDate: {today.isoformat()}\nTime: {time_str}\n\nPlease select a date:",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data.startswith("cal:"))
async def nav_calendar_handler(callback: CallbackQuery):
    _, year, month = callback.data.split(":")
    today = keyboards.get_tehran_today()
    kb = keyboards.calendar_keyboard(int(year), int(month), today)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("day:"))
async def process_day(callback: CallbackQuery):
    _, selected_date = callback.data.split(":", 1)
    user_id = callback.from_user.id
    tasks = database.get(user_id, selected_date)
    kb = keyboards.main_keyboard(tasks, selected_date)
    await callback.message.edit_text(f"Tasks for {selected_date}\nChoose an option:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("add:"))
async def add_handler(callback: CallbackQuery, state: FSMContext):
    _, selected_date = callback.data.split(":", 1)

    if keyboards.is_past_date(selected_date):
        await callback.answer("⚠️ This date has already passed! You cannot add new tasks.", show_alert=True)
        user_id = callback.from_user.id
        tasks = database.get(user_id, selected_date)
        kb = keyboards.main_keyboard(tasks, selected_date)
        await callback.message.edit_reply_markup(reply_markup=kb)
        return

    await state.update_data(current_date=selected_date)
    kb = keyboards.cancel_keyboard()
    await callback.message.edit_text("Please enter the task text:", reply_markup=kb)
    await state.set_state(Task.wait_for_text)
    await callback.answer()

@router.message(Task.wait_for_text, F.text, ~F.text.startswith("/"))
async def process_new_task_text(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text)
    h, m = get_default_time()
    await message.answer("⏰ Please set the time:", reply_markup=keyboards.time_picker_keyboard(h, m))
    await state.set_state(Task.wait_for_time)

@router.callback_query(F.data.startswith("task:"))
async def task_menu_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if not task:
        await callback.answer("⚠️ Task not found!", show_alert=True)
        return

    if keyboards.is_past_date(task_date) and task["status"] == "done":
        archive_text = (
            f"🗄 **Archive Details**\n\n"
            f"📌 **Task:** {task['task_text']}\n"
            f"🟢 **Status:** Done\n"
            f"📅 **Date:** {task['task_date']}\n"
            f"⏰ **Time:** {task['task_time']}"
        )
        kb = keyboards.archive_keyboard(task_id, task_date)
        await callback.message.edit_text(archive_text, reply_markup=kb, parse_mode="Markdown")

    elif keyboards.is_past_date(task_date) and task["status"] == "pending":
        kb = keyboards.task_keyboard(task_id, task_date, task["status"])
        await callback.message.edit_text(f"⚠️ This task is OVERDUE!\n\n📌 {task['task_text']}\n\nChoose an option:", reply_markup=kb)

    else:
        kb = keyboards.task_keyboard(task_id, task_date, task["status"])
        if task["status"] == "done":
            await callback.message.edit_text(f"✅ This task is completed.\n\n📌 {task['task_text']}\n\nChoose an option:", reply_markup=kb)
        else:
            await callback.message.edit_text(f"Choose an option for this task:\n\n📌 {task['task_text']}", reply_markup=kb)

    await callback.answer()

@router.callback_query(F.data.startswith("undone:"))
async def undone_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id
    database.edit_task_status(task_id, user_id, "pending")

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if task:
        kb = keyboards.task_keyboard(task_id, task_date, task["status"])
        await callback.message.edit_text(f"🔄 Task reopened.\n\nChoose an option for this task:\n\n📌 {task['task_text']}", reply_markup=kb)
    else:
        await callback.message.edit_text("⚠️ Error reopening task.")
    await callback.answer()

@router.callback_query(F.data.startswith("copy_today:"))
async def copy_today_prompt_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    kb = keyboards.copy_time_prompt_keyboard(task_id, task_date)
    await callback.message.edit_text("How would you like to set the time for the copied task?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("copy_same:"))
async def copy_same_time_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if task:
        today_str = keyboards.get_tehran_today().isoformat()
        task_time = task["task_time"]
        priority = task.get("priority", "normal")

        if is_past_time(today_str, task_time):
            await callback.answer("⚠️ That time has already passed today! Please set a new time.", show_alert=True)
            await state.update_data(
                current_date=today_str,
                task_text=task["task_text"],
                original_date=task_date,
                is_copy=True,
                priority=priority
            )
            await state.set_state(Task.wait_for_time)
            h, m = get_default_time()
            await callback.message.edit_text("⏰ Please set the new time for today:", reply_markup=keyboards.time_picker_keyboard(h, m))
            return

        if database.check_overlap(user_id, today_str, task_time):
            await state.update_data(
                current_date=today_str,
                task_text=task["task_text"],
                task_time=task_time,
                original_date=task_date,
                is_copy=True,
                priority=priority
            )
            overlap_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Set Anyway", callback_data="force_save")],
                [InlineKeyboardButton(text="Change Time", callback_data="change_time")],
                [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
            ])
            await callback.message.edit_text(
                f"Overlap Warning!\nYou already have a task at {task_time} on {today_str}.\nWhat would you like to do?",
                reply_markup=overlap_keyboard
            )
            await callback.answer()
            return

        database.add(user_id, task["task_text"], today_str, task_time, priority)
        old_tasks = database.get(user_id, task_date)
        kb = keyboards.main_keyboard(old_tasks, task_date)
        await callback.message.edit_text(f"✅ Task copied to today!\nTasks for {task_date}:", reply_markup=kb)

    await callback.answer()



@router.callback_query(F.data.startswith("copy_new:"))
async def copy_new_time_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if task:
        today_str = keyboards.get_tehran_today().isoformat()
        await state.update_data(
            current_date=today_str,
            task_text=task["task_text"],
            original_date=task_date,
            is_copy=True,
            priority=task.get("priority", "normal")
        )
        await state.set_state(Task.wait_for_time)

        h, m = get_default_time()
        await callback.message.edit_text("⏰ Please set the new time for today:", reply_markup=keyboards.time_picker_keyboard(h, m))

    await callback.answer()

@router.callback_query(F.data.startswith("delete_req:"))
async def delete_request_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    kb = keyboards.delete_confirm_keyboard(task_id, task_date)
    await callback.message.edit_text("⚠️ Are you sure you want to delete this task?\nThis action cannot be undone.", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id
    database.delete(task_id, user_id)
    tasks = database.get(user_id, task_date)
    kb = keyboards.main_keyboard(tasks, task_date)
    await callback.message.edit_text(f"✅ Task permanently deleted.\n\nTasks for {task_date}:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("done:"))
async def done_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    database.edit_task_status(task_id, user_id, "done")

    database.delete_all_reminders(task_id, user_id)

    tasks = database.get(user_id, task_date)
    kb = keyboards.main_keyboard(tasks, task_date)
    await callback.message.edit_text(f"✅ Task marked as done.\nAll active reminders removed.\n\nTasks for {task_date}:", reply_markup=kb)
    await callback.answer()



@router.callback_query(F.data.startswith("edit_menu:"))
async def edit_menu_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    if keyboards.is_past_date(task_date):
        await callback.answer("⚠️ Past tasks can only be rescheduled or marked as done.", show_alert=True)
        kb = keyboards.task_keyboard(task_id, task_date)
        await callback.message.edit_reply_markup(reply_markup=kb)
        return

    kb = keyboards.edit_keyboard(task_id, task_date)
    await callback.message.edit_text("What would you like to edit?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("edit_text:"))
async def edit_text_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    await state.update_data(task_id=task_id, original_date=task_date)
    await state.set_state(Task.wait_for_edit_text)
    await callback.message.edit_text("Please write your new task text:", reply_markup=keyboards.cancel_keyboard())
    await callback.answer()

@router.message(Task.wait_for_edit_text, F.text, ~F.text.startswith("/"))
async def process_edit_task_text(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    original_date = data.get("original_date")

    try:
        database.edit_task_text(data.get("task_id"), user_id, message.text)
    except ValueError:
        await message.answer("Task Text cannot be empty.")
        return

    await state.clear()
    tasks = database.get(user_id, original_date)
    await message.answer(f"Text updated.\nTasks for {original_date}:", reply_markup=keyboards.main_keyboard(tasks, original_date))

@router.callback_query(F.data.startswith("edit_date:"))
async def edit_date_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    await state.update_data(task_id=task_id, original_date=task_date)
    kb = keyboards.edit_date_calendar_keyboard(task_date, task_id)
    await callback.message.edit_text("Select a new date for this task:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("edit_date_pick:"))
async def edit_date_pick_handler(callback: CallbackQuery):
    _, task_id, new_date = callback.data.split(":")
    if keyboards.is_past_date(new_date):
        await callback.answer("⚠️ You cannot reschedule a task to a past date!", show_alert=True)
        return

    kb = keyboards.edit_time_prompt_keyboard(task_id, new_date)
    await callback.message.edit_text(f"Date selected: {new_date}\nDo you want to edit the time as well?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("no_edit_time:"))
async def no_edit_time_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, new_date = callback.data.split(":")
    user_id = callback.from_user.id
    data = await state.get_data()
    original_date = data.get("original_date", new_date)

    tasks = database.get(user_id, original_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if not task:
        await callback.answer("⚠️ Task not found!", show_alert=True)
        return

    task_time = task["task_time"]

    if is_past_time(new_date, task_time):
        await callback.answer("⚠️ That time has already passed! You must pick a new time.", show_alert=True)
        await state.update_data(task_id=task_id, target_date=new_date, original_date=original_date)
        await state.set_state(Task.wait_for_edit_time)
        h, m = get_default_time()
        await callback.message.edit_text("Please set the new time:", reply_markup=keyboards.time_picker_keyboard(h, m))
        return

    if database.check_overlap(user_id, new_date, task_time):
        await state.update_data(task_id=task_id, target_date=new_date, original_date=original_date, task_time=task_time)
        overlap_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Set Anyway", callback_data="force_edit")],
            [InlineKeyboardButton(text="Change Time", callback_data="change_edit_time")],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
        ])
        await callback.message.edit_text(f"Overlap Warning!\nYou already have a task at {task_time} on {new_date}.\nWhat would you like to do?", reply_markup=overlap_keyboard)
        await callback.answer()
        return

    database.edit_task_date(task_id, user_id, new_date)
    await state.clear()
    updated_tasks = database.get(user_id, original_date)
    kb = keyboards.main_keyboard(updated_tasks, original_date)
    await callback.message.edit_text(f"Task moved to {new_date}!\nTasks for {original_date}:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("yes_edit_time:"))
async def yes_edit_time_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, new_date = callback.data.split(":")
    await state.update_data(task_id=task_id, target_date=new_date)
    await state.set_state(Task.wait_for_edit_time)
    h, m = get_default_time()
    await callback.message.edit_text("Please set the new time:", reply_markup=keyboards.time_picker_keyboard(h, m))
    await callback.answer()

@router.callback_query(F.data.startswith("edit_time:"))
async def edit_time_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    await state.update_data(task_id=task_id, target_date=task_date, original_date=task_date)
    await state.set_state(Task.wait_for_edit_time)
    h, m = get_default_time()
    await callback.message.edit_text("Please set the new time:", reply_markup=keyboards.time_picker_keyboard(h, m))
    await callback.answer()

@router.callback_query(F.data == "change_time")
@router.callback_query(F.data == "change_edit_time")
async def change_time_generic(callback: CallbackQuery):
    h, m = get_default_time()
    await callback.message.edit_text("Please set the time:", reply_markup=keyboards.time_picker_keyboard(h, m))
    await callback.answer()

@router.callback_query(F.data.startswith("tp:"))
async def process_time_picker(callback: CallbackQuery, state: FSMContext):
    _, action, h_str, m_str = callback.data.split(":")
    hour, minute = int(h_str), int(m_str)

    if action == "h3u": hour = (hour + 3) % 24
    elif action == "h1u": hour = (hour + 1) % 24
    elif action == "m15u": minute = (minute + 15) % 60
    elif action == "m5u": minute = (minute + 5) % 60
    elif action == "h3d": hour = (hour - 3) % 24
    elif action == "h1d": hour = (hour - 1) % 24
    elif action == "m15d": minute = (minute - 15) % 60
    elif action == "m5d": minute = (minute - 5) % 60
    elif action == "flip": hour = (hour + 12) % 24

    if action != "confirm":
        await callback.message.edit_reply_markup(reply_markup=keyboards.time_picker_keyboard(hour, minute))
        await callback.answer()
        return

    task_time = f"{hour:02d}:{minute:02d}"
    await state.update_data(task_time=task_time)

    data = await state.get_data()
    user_id = callback.from_user.id
    current_state = await state.get_state()

    is_editing = (current_state == Task.wait_for_edit_time.state)
    is_custom_rem = (current_state == Task.wait_for_rem_time.state)


    if is_custom_rem:
        rem_date = data.get("rem_date")
        task_id = data.get("task_id")
        original_date = data.get("original_date")

        if is_past_time(rem_date, task_time):
            await callback.answer("⏰ You cannot schedule a reminder in the past!", show_alert=True)
            return

        tasks = database.get(user_id, original_date)
        task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

        if task:
            y1, m1, d1 = map(int, rem_date.split("-"))
            h1, min1 = map(int, task_time.split(":"))
            rem_dt = jdatetime.datetime(y1, m1, d1, h1, min1)

            y2, m2, d2 = map(int, task["task_date"].split("-"))
            h2, min2 = map(int, task["task_time"].split(":"))
            task_dt = jdatetime.datetime(y2, m2, d2, h2, min2)

            if rem_dt > task_dt:
                await callback.answer("⚠️ Reminder cannot be set AFTER the task's due time!", show_alert=True)
                return

            existing_rems = database.get_reminders(task_id, user_id)
            for r in existing_rems:
                if r["remind_date"] == rem_date and r["remind_time"] == task_time:
                    await callback.answer("⚠️ You already have a reminder at this exact time!", show_alert=True)
                    return

        database.add_reminder(task_id, user_id, rem_date, task_time)
        await state.clear()

        rems = database.get_reminders(task_id, user_id)
        kb = keyboards.reminders_management_keyboard(task_id, original_date, rems)
        await callback.message.edit_text("✅ Custom reminder added!", reply_markup=kb)
        await callback.answer()
        return


    target_date = data.get("target_date") if is_editing else data.get("current_date")
    original_date = data.get("original_date", target_date)

    if is_past_time(target_date, task_time):
        await callback.answer("⏰ You cannot schedule a task in the past!", show_alert=True)
        return

    if database.check_overlap(user_id, target_date, task_time):
        callback_prefix = "force_edit" if is_editing else "force_save"
        change_prefix = "change_edit_time" if is_editing else "change_time"

        overlap_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Set Anyway", callback_data=callback_prefix)],
            [InlineKeyboardButton(text="Change Time", callback_data=change_prefix)],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel")]
        ])
        await callback.message.edit_text(
            f"Overlap Warning!\nYou already have a task at {task_time} on {target_date}.\nWhat would you like to do?",
            reply_markup=overlap_keyboard
        )

    else:
        if is_editing:
            database.edit_task_date(data.get("task_id"), user_id, target_date)
            database.edit_task_time(data.get("task_id"), user_id, task_time)
            tasks = database.get(user_id, original_date)
            await callback.message.edit_text(
                f"Time updated to {task_time}!\nTasks for {original_date}:",
                reply_markup=keyboards.main_keyboard(tasks, original_date)
            )
            await state.clear()


        else:
            if data.get("is_copy"):
                task_id = database.add(user_id, data.get("task_text"), target_date, task_time, data.get("priority", "normal"))
                await state.clear()
                kb = keyboards.after_add_keyboard(target_date, task_id)
                await callback.message.edit_text(
                    f"✅ Task saved at {task_time}!\n\nWould you like to add a reminder?",
                    reply_markup=kb
                )
            else:
                await state.update_data(target_date=target_date, task_time=task_time)
                await state.set_state(Task.wait_for_priority)
                await callback.message.edit_text(
                    "How important is this task?",
                    reply_markup=keyboards.priority_keyboard()
                )

    await callback.answer()



@router.callback_query(F.data == "force_save")
async def force_save_add(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("is_copy"):
        user_id = callback.from_user.id
        current_date = data.get("current_date")
        task_id = database.add(user_id, data.get("task_text"), current_date, data.get("task_time"), data.get("priority", "normal"))
        await state.clear()
        kb = keyboards.after_add_keyboard(current_date, task_id)
        await callback.message.edit_text("✅ Task saved!\n\nWould you like to add a reminder?", reply_markup=kb)
    else:
        await state.set_state(Task.wait_for_priority)
        await callback.message.edit_text("How important is this task?", reply_markup=keyboards.priority_keyboard())
    await callback.answer()



@router.callback_query(F.data == "force_edit")
async def force_save_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id
    target_date = data.get("target_date")
    original_date = data.get("original_date", target_date)

    database.edit_task_date(data.get("task_id"), user_id, target_date)
    database.edit_task_time(data.get("task_id"), user_id, data.get("task_time"))
    await state.clear()

    tasks = database.get(user_id, original_date)
    await callback.message.edit_text(f"Time updated!\nTasks for {original_date}:", reply_markup=keyboards.main_keyboard(tasks, original_date))
    await callback.answer()



@router.callback_query(F.data.startswith("rem_menu:"))
async def rem_menu_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if not task:
        await callback.answer("⚠️ Task not found!", show_alert=True)
        return

    if is_past_time(task_date, task["task_time"]):
        await callback.answer("⚠️ This task's time has already passed! You cannot set reminders for it.", show_alert=True)
        return

    rems = database.get_reminders(task_id, user_id)
    kb = keyboards.reminders_management_keyboard(task_id, task_date, rems)

    text = f"🔔 **Reminders for:**\n📌 {task['task_text']}\n\n"
    if not rems:
        text += "No reminders set yet."
    else:
        text += "Your active reminders:"

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("add_rem_menu:"))
async def add_rem_menu_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if not task:
        await callback.answer("⚠️ Task not found!", show_alert=True)
        return

    if is_past_time(task_date, task["task_time"]):
        await callback.answer("⚠️ This task's time has already passed!", show_alert=True)
        return

    await state.update_data(selected_rems=[])
    kb = keyboards.reminder_toggle_keyboard(task_id, task_date, [])
    await callback.message.edit_text("Select relative times to be reminded:", reply_markup=kb)
    await callback.answer()



@router.callback_query(F.data.startswith("toggle_rem:"))
async def toggle_rem_handler(callback: CallbackQuery, state: FSMContext):
    _, opt, task_id, task_date = callback.data.split(":")
    data = await state.get_data()
    selected = data.get("selected_rems", [])

    if opt in selected:
        selected.remove(opt)
    else:
        selected.append(opt)

    await state.update_data(selected_rems=selected)
    kb = keyboards.reminder_toggle_keyboard(task_id, task_date, selected)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("save_rems:"))
async def save_rems_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id
    data = await state.get_data()
    selected = data.get("selected_rems", [])

    if not selected:
        await callback.answer("⚠️ Please select at least one option!", show_alert=True)
        return

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    skipped_any = False

    if task:
        y, m, d = map(int, task["task_date"].split("-"))
        h, minute = map(int, task["task_time"].split(":"))

        task_dt = jdatetime.datetime(y, m, d, h, minute)

        tehran_now = datetime.now(pytz.timezone("Asia/Tehran")).replace(tzinfo=None)
        now_j = jdatetime.datetime.fromgregorian(datetime=tehran_now)

        for opt in selected:
            delta = timedelta()
            if opt == "5m": delta = timedelta(minutes=5)
            elif opt == "15m": delta = timedelta(minutes=15)
            elif opt == "30m": delta = timedelta(minutes=30)
            elif opt == "1h": delta = timedelta(hours=1)
            elif opt == "1d": delta = timedelta(days=1)

            rem_dt = task_dt - delta

            if rem_dt <= now_j:
                skipped_any = True
                continue

            rem_date_str = f"{rem_dt.year:04d}-{rem_dt.month:02d}-{rem_dt.day:02d}"
            rem_time_str = f"{rem_dt.hour:02d}:{rem_dt.minute:02d}"

            database.add_reminder(task_id, user_id, rem_date_str, rem_time_str)

    await state.update_data(selected_rems=[])
    rems = database.get_reminders(task_id, user_id)
    kb = keyboards.reminders_management_keyboard(task_id, task_date, rems)

    if skipped_any:
        await callback.answer("⚠️ Some reminders were skipped because their time had already passed!", show_alert=True)
        await callback.message.edit_text("✅ Valid reminders successfully saved!", reply_markup=kb)
    else:
        await callback.message.edit_text("✅ Reminders successfully saved!", reply_markup=kb)

    await callback.answer()



@router.callback_query(F.data.startswith("del_rem_req:"))
async def del_rem_req_handler(callback: CallbackQuery):
    _, rem_id, task_id, task_date = callback.data.split(":")
    kb = keyboards.delete_reminder_confirm_keyboard(rem_id, task_id, task_date)
    await callback.message.edit_text("⚠️ Are you sure you want to delete this reminder?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_del_rem:"))
async def confirm_del_rem_handler(callback: CallbackQuery):
    _, rem_id, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id
    database.delete_reminder(rem_id, user_id)

    rems = database.get_reminders(task_id, user_id)
    kb = keyboards.reminders_management_keyboard(task_id, task_date, rems)
    await callback.message.edit_text("✅ Reminder deleted.", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("custom_rem:"))
async def custom_rem_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date = callback.data.split(":")
    kb = keyboards.rem_date_calendar_keyboard(task_id, task_date)
    await callback.message.edit_text("Select a date for your custom reminder:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    return_date = data.get("original_date") or data.get("current_date")
    await state.clear()

    if return_date:
        tasks = database.get(callback.from_user.id, return_date)
        kb = keyboards.main_keyboard(tasks, return_date)
        await callback.message.edit_text(f"Operation cancelled.\nTasks for {return_date}:", reply_markup=kb)
    else:
        await callback.message.edit_text("Operation cancelled. Please send /start again.")
    await callback.answer()



@router.callback_query(F.data.startswith("rem_date_pick:"))
async def rem_date_pick_handler(callback: CallbackQuery, state: FSMContext):
    _, task_id, task_date, rem_date = callback.data.split(":")

    if rem_date > task_date:
        await callback.answer("⚠️ Reminder date cannot be after the task date!", show_alert=True)
        return

    await state.update_data(task_id=task_id, original_date=task_date, rem_date=rem_date)
    await state.set_state(Task.wait_for_rem_time)

    h, m = get_default_time()
    await callback.message.edit_text(f"📅 Date: {rem_date}\n⏰ Please set the exact time:", reply_markup=keyboards.time_picker_keyboard(h, m))
    await callback.answer()


@router.callback_query(F.data == "rem_got_it")
async def rem_got_it_handler(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("rem_done:"))
async def rem_done_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    database.edit_task_status(task_id, user_id, "done")


    database.delete_all_reminders(task_id, user_id)

    await callback.message.edit_text("✅ Task successfully marked as done!", reply_markup=None)
    await callback.answer()


@router.callback_query(F.data.startswith("rem_manage:"))
async def rem_manage_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    user_id = callback.from_user.id

    tasks = database.get(user_id, task_date)
    task = next((t for t in tasks if str(t['id']) == str(task_id)), None)

    if not task:
        await callback.answer("⚠️ Task not found!", show_alert=True)
        return

    kb = keyboards.task_keyboard(task_id, task_date, task["status"])
    await callback.message.edit_text(f"Choose an option for this task:\n\n📌 {task['task_text']}", reply_markup=kb)
    await callback.answer()



@router.callback_query(F.data.startswith("new_prio:"))
async def new_priority_handler(callback: CallbackQuery, state: FSMContext):
    _, priority = callback.data.split(":")
    data = await state.get_data()
    user_id = callback.from_user.id

    target_date = data.get("target_date") or data.get("current_date")
    task_time = data.get("task_time")
    task_text = data.get("task_text")

    task_id = database.add(user_id, task_text, target_date, task_time, priority)

    await state.clear()
    kb = keyboards.after_add_keyboard(target_date, task_id)
    await callback.message.edit_text(f"✅ Task saved at {task_time}!\n\nWould you like to add a reminder?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("edit_prio_menu:"))
async def edit_prio_menu_handler(callback: CallbackQuery):
    _, task_id, task_date = callback.data.split(":")
    kb = keyboards.edit_priority_keyboard(task_id, task_date)
    await callback.message.edit_text("Select the new priority:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("set_prio:"))
async def set_prio_handler(callback: CallbackQuery):
    _, task_id, task_date, new_prio = callback.data.split(":")
    user_id = callback.from_user.id

    database.edit_task_priority(task_id, user_id, new_prio)

    tasks = database.get(user_id, task_date)
    kb = keyboards.main_keyboard(tasks, task_date)
    await callback.message.edit_text(f"✅ Priority updated!\n\nTasks for {task_date}:", reply_markup=kb)
    await callback.answer()
