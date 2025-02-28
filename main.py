import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from models.database import init_db
from handlers.user import router as user_router

TOKEN = "7702332807:AAHgFpGZbSzd0VxOL6oFGWT7BOKWq5kk21E"


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await init_db()  
    dp.include_router(user_router)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())


