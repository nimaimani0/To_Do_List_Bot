import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from datetime import datetime
import jdatetime

import database
import handlers
import keyboards

API_TOKEN = os.getenv("BOT_TOKEN")


async def check_reminders(bot: Bot):
    tehran_tz = pytz.timezone("Asia/Tehran")
    now = datetime.now(tehran_tz)
    current_date = jdatetime.date.fromgregorian(date=now.date()).isoformat()
    current_time = now.strftime("%H:%M")

    due_reminders = database.get_due_reminders(current_date, current_time)

    for rem in due_reminders:
        task_date = rem['task_date']
        text = (
            f"🔔 **Reminder!**\n\n"
            f"📌 **Task:** {rem['task_text']}\n"
            f"⏰ **Due:** {rem['task_time']} ({task_date})"
        )
        kb = keyboards.reminder_notification_keyboard(rem['task_id'], task_date)

        try:
            await bot.send_message(chat_id=rem['user_id'], text=text, reply_markup=kb, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Failed to send reminder to {rem['user_id']}: {e}")

        database.delete_reminder(rem['reminder_id'], rem['user_id'])

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    dp.include_router(handlers.router)
    database.init()

    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tehran"))
    scheduler.add_job(check_reminders, "cron", args=[bot], minute="*")
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
