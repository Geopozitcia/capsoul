from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def contact_keyboard():
    button = KeyboardButton(text="📱 Отправить контакт", request_contact=True)

    markup = ReplyKeyboardMarkup(
        keyboard=[[button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup