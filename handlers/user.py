from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from keyboards.reply_kb import contact_keyboard
import aiosqlite

router = Router()

DB_NAME = "CAPSOUL.db"


@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username
    username = f"@{username}" if username else "Не указан"

    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, существует ли пользователь в базе
        cursor = await db.execute("SELECT id, phone FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()

        # Если пользователя нет, добавляем его
        if not user:
            await db.execute("""
                INSERT OR IGNORE INTO users (id, name, user_name, phone)
                VALUES (?, ?, ?, ?)""", (user_id, name, username, ""))
            await db.commit()

        # Если номер телефона не найден, запрашиваем его
        if not user or not user[1]:
            await message.answer(
                f"Здравствуйте, {name}! Меня зовут Капсула, я ваш умный помощник из студии дизайна интерьеров Capsoul.\n"
                f"Для начала запишем ваш номер телефона. Он нужен только для связи с вами. Обещаем - спама не будет",
                reply_markup=await contact_keyboard()
            )
        else:
            await message.answer(
                f"Здравствуйте, {name}. Что вы хотите сделать?",
                reply_markup=ReplyKeyboardRemove()
            )


@router.message(F.content_type == types.ContentType.CONTACT)
async def get_contact(message: types.Message):
    contact = message.contact
    user_id = message.from_user.id
    phone = contact.phone_number

    async with aiosqlite.connect(DB_NAME) as db:
        # Обновляем номер телефона пользователя в базе
        await db.execute("""
            UPDATE users SET phone = ? WHERE id = ?""", (phone, user_id))
        await db.commit()

    await message.answer(
        "Спасибо! Ваш номер телефона сохранён.\nДавайте уточним ваши пожелания к дизайн проекту.",
        reply_markup=ReplyKeyboardRemove()
    )