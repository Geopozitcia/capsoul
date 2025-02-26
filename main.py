import asyncio
import logging
from aiogram import Bot, Dispatcher
from models.database import init_db
from handlers.user import router as user_router

TOKEN = "7702332807:AAHgFpGZbSzd0VxOL6oFGWT7BOKWq5kk21E"


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    await init_db()  # Инициализация базы данных
    dp.include_router(user_router)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())