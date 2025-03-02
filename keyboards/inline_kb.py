from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utilits.codes.google_calendar import *

def get_time_keyboard(date):
    """Создает клавиатуру с доступным временем."""
    service = authenticate_google_calendar()
    available_times = get_available_times_for_date(service, date)

    buttons = []
    for i in range(0, len(available_times), 2): 
        row = [
            InlineKeyboardButton(text=available_times[i], callback_data=f"time_{available_times[i]}"),
            InlineKeyboardButton(text=available_times[i + 1], callback_data=f"time_{available_times[i + 1]}")
        ] if i + 1 < len(available_times) else [
            InlineKeyboardButton(text=available_times[i], callback_data=f"time_{available_times[i]}")
        ]
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard():
    """Создает клавиатуру с основными действиями."""
    buttons = [
        [InlineKeyboardButton(text="Моя консультация", callback_data="my_consultation")],
        [InlineKeyboardButton(text="Добавить планировку", callback_data="add_planning")],
        [InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_panel():
    """Создает клавиатуру для админа."""
    buttons = [
        [InlineKeyboardButton(text="Статистика", callback_data="get_statistic")],
        [InlineKeyboardButton(text="Отправить напоминание", callback_data="send_remainder")],
        [InlineKeyboardButton(text="Синхронизация БД", callback_data="sync_database")],
        [InlineKeyboardButton(text="Планировки", callback_data="get_planfiles")],
        [InlineKeyboardButton(text="Календарь/GSheets", callback_data="get_links")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)