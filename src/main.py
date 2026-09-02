import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

import database
import handlers


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    database.init()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)

    print("Bot is starting...")

    await dp.start_polling(bot)

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
