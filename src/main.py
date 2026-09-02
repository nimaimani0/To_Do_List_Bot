import asyncio
import logging
from aiogram import Bot, Dispatcher

import database
import handlers

BOT_TOKEN = "8903844663:AAEVDAZ_jEl3HT9eAdCrSzWtAYnRUyDfxl0"

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
