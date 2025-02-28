from aiogram import Bot, Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from models.database import DB_NAME
import aiosqlite
from datetime import datetime
import asyncio
from pathlib import Path
from keyboards.reply_kb import get_more_files_keyboard, get_confirmation_keyboard
from keyboards.inline_kb import admin_panel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import sqlite3


router = Router()

class ReminderState(StatesGroup):
    text = State()  # Состояние для ввода текста напоминания
    time = State()  # Состояние для ввода времени
    photo = State()  # Состояние для загрузки фотографии
    confirm = State()  # Состояние для подтверждения

class GetPlanningState(StatesGroup):
    phone = State()  # Состояние для ввода номера телефона

@router.callback_query(lambda c: c.data == "get_statistic")
async def get_statistic(callback_query: types.CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = await cursor.fetchone()
        await callback_query.message.answer(f"Количество пользователей: {count[0]}")

@router.callback_query(lambda c: c.data == "send_remainder")
async def send_remainder_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите текст напоминания:")
    await state.set_state(ReminderState.text)

@router.message(ReminderState.text)
async def process_remainder_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Введите время отправки в формате дд.мм.гггг чч:мм:")
    await state.set_state(ReminderState.time)

@router.message(ReminderState.time)
async def process_remainder_time(message: Message, state: FSMContext, bot: Bot):
    try:
        # Парсим введенное время
        reminder_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        current_time = datetime.now()

        # Проверяем, что время в будущем
        if reminder_time <= current_time:
            await message.answer("Время должно быть в будущем. Попробуйте снова.")
            return

        # Получаем текст из состояния
        data = await state.get_data()
        reminder_text = data.get("text")

        # Сохраняем время и текст в состоянии
        await state.update_data(time=reminder_time, text=reminder_text)

        # Спрашиваем, хочет ли админ приложить фотографию
        await message.answer(
            "Хотите приложить фотографию?",
            reply_markup=get_more_files_keyboard()  # Используем reply-кнопки
        )
        await state.set_state(ReminderState.photo)

    except ValueError:
        await message.answer("Неверный формат времени. Используйте формат дд.мм.гггг чч:мм.")

@router.message(ReminderState.photo)
async def process_remainder_photo(message: Message, state: FSMContext, bot: Bot):
    # Если админ отправляет фотографию
    if message.photo:
        # Сохраняем фотографию
        photo_id = message.photo[-1].file_id
        photo_file = await bot.get_file(photo_id)
        photo_path = Path("utilits/images/remainders") / f"{photo_id}.jpg"
        await bot.download_file(photo_file.file_path, destination=photo_path)

        # Сохраняем путь к фотографии в состоянии
        await state.update_data(photo=str(photo_path))

        data = await state.get_data()
        reminder_text = data.get("text")
        reminder_time = data.get("time")

        # Показываем предварительный просмотр напоминания
        await message.answer(
            f"Это ваше напоминание:\n\n"
            f"Текст: {reminder_text}\n"
            f"Дата: {reminder_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Хотите что-нибудь изменить или отменить отправку напоминания?",
            reply_markup=get_confirmation_keyboard()  # Новые кнопки для подтверждения
        )
        await state.set_state(ReminderState.confirm)
    # Если админ выбирает "Да" или "Нет"
    elif message.text in ["Да", "Нет"]:
        if message.text == "Да":
            await message.answer("Отправьте фотографию.")
        else:
            data = await state.get_data()
            reminder_text = data.get("text")
            reminder_time = data.get("time")

            # Показываем предварительный просмотр напоминания
            await message.answer(
                f"Это ваше напоминание:\n\n"
                f"Текст: {reminder_text}\n"
                f"Дата: {reminder_time.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Хотите что-нибудь изменить или отменить отправку напоминания?",
                reply_markup=get_confirmation_keyboard()  # Новые кнопки для подтверждения
            )
            await state.set_state(ReminderState.confirm)
    else:
        await message.answer("Пожалуйста, используйте кнопки.")

@router.message(ReminderState.confirm)
async def process_remainder_confirm(message: Message, state: FSMContext, bot: Bot):
    if message.text == "Сохранить":
        data = await state.get_data()
        reminder_text = data.get("text")
        reminder_time = data.get("time")
        photo_path = data.get("photo")

        # Запланировать отправку напоминания
        delay = (reminder_time - datetime.now()).total_seconds()
        asyncio.create_task(send_remainder_to_all(bot, reminder_text, delay, photo_path))

        await message.answer(
            f"Напоминание запланировано на {reminder_time.strftime('%d.%m.%Y %H:%M')}.",
            reply_markup=admin_panel()
        )
        await state.clear()
    elif message.text == "Изменить":
        await message.answer("Введите текст напоминания:")
        await state.set_state(ReminderState.text)
    elif message.text == "Отменить":
        await message.answer("Отправка напоминания отменена.", reply_markup=admin_panel())
        await state.clear()
    else:
        await message.answer("Пожалуйста, используйте кнопки.")

@router.callback_query(lambda c: c.data == "get_planfiles")
async def get_planfiles_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите номер телефона пользователя:")
    await state.set_state(GetPlanningState.phone)

@router.message(GetPlanningState.phone)
async def process_get_planfiles_phone(message: Message, state: FSMContext):
    phone = message.text

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, planning_file FROM users WHERE phone = ?", (phone,))
        user = await cursor.fetchone()

        if not user:
            await message.answer("Пользователь с таким номером телефона не найден.")
            await state.clear()
            return

        user_id, planning_file = user

        if not planning_file:
            await message.answer("У пользователя нет загруженных файлов.")
            await state.clear()
            return

        # Отправляем все файлы из папки
        folder_path = Path("storage") / planning_file
        if not folder_path.exists():
            await message.answer("Папка с файлами не найдена.")
            await state.clear()
            return

        for file in folder_path.iterdir():
            if file.is_file():
                await message.answer_document(FSInputFile(file))

        await message.answer("Все файлы отправлены.", reply_markup=admin_panel())
        await state.clear()

async def send_remainder_to_all(bot: Bot, text: str, delay: float, photo_path: str = None):
    """Отправляет напоминание всем пользователям через указанное время."""
    await asyncio.sleep(delay)  # Ждем указанное время

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id FROM users")
        users = await cursor.fetchall()

        for user in users:
            user_id = user[0]
            try:
                if photo_path:
                    # Отправляем фотографию из локального файла
                    await bot.send_photo(user_id, FSInputFile(photo_path), caption=text)
                else:
                    await bot.send_message(user_id, text)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

def sync_database_to_google_sheets_sync():
    """Синхронная версия функции синхронизации."""
    try:
        # Настройка аутентификации
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("utilits/codes/key.json", scope)
        client = gspread.authorize(creds)

        # Открываем таблицу по ID
        sheet = client.open_by_key("1jFnTiutAYa1C1PQV0VnYgtu-q033aKdnIs1WVBQrxOk")
        worksheet = sheet.get_worksheet(0)  # Выбираем первый лист

        # Очищаем лист перед записью новых данных
        worksheet.clear()

        # Читаем данные из базы данных
        with sqlite3.connect(DB_NAME) as db:
            cursor = db.execute("SELECT * FROM users")
            users = cursor.fetchall()

            # Записываем заголовки столбцов
            headers = ["ID", "Name", "Phone", "Username", "Aim of Project", "Past Experience", "Team Exist", "Date of Project", "Design Preferences", "Meeting Date", "Planning File"]
            worksheet.append_row(headers)

            # Записываем данные
            for user in users:
                worksheet.append_row(user)
    except Exception as e:
        raise e

async def sync_database_to_google_sheets():
    """Асинхронная обертка для синхронной функции."""
    await asyncio.to_thread(sync_database_to_google_sheets_sync)

@router.callback_query(lambda c: c.data == "sync_database")
async def sync_database_handler(callback_query: types.CallbackQuery):
    try:
        await sync_database_to_google_sheets()
        await callback_query.message.answer("База данных успешно синхронизирована с Google Таблицей.", reply_markup=admin_panel())
    except Exception as e:
        logging.error(f"Ошибка при синхронизации: {e}", exc_info=True)
        await callback_query.message.answer(f"Ошибка при синхронизации: {e}", reply_markup=admin_panel())