from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def contact_keyboard():
    button = KeyboardButton(text="📱 Отправить контакт", request_contact=True)
    markup = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True)
    return markup

def get_aim_keyboard():
    buttons = [
        [KeyboardButton(text="Для личного проживания")],
        [KeyboardButton(text="Для инвестиций (аренда, продажа)")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_experience_keyboard():
    buttons = [
        [KeyboardButton(text="Да, был положительный опыт")],
        [KeyboardButton(text="Да, но опыт был неудачным")],
        [KeyboardButton(text="Нет, это мой первый проект с дизайнером")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_team_keyboard():
    buttons = [
        [KeyboardButton(text="Да, есть проверенная команда")],
        [KeyboardButton(text="Нет, пока ищу специалистов")],
        [KeyboardButton(text="Еще не думал(а) об этом")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_date_keyboard():
    buttons = [
        [KeyboardButton(text="В ближайшее время")],
        [KeyboardButton(text="Через 2-3 месяца")],
        [KeyboardButton(text="Без особой спешки")],
        [KeyboardButton(text="Еще не скоро")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_style_keyboard():
    buttons = [
        [KeyboardButton(text="Первый вариант")],
        [KeyboardButton(text="Второй вариант")],
        [KeyboardButton(text="Третий вариант")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_final_decision_keyboard():
    buttons = [
        [KeyboardButton(text="Мне нравятся эти решения")],
        [KeyboardButton(text="Думаю, мне нужно что-то более индивидуальное")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_planning_keyboard():
    buttons = [
        [KeyboardButton(text="Нет планировки")],
        [KeyboardButton(text="Прикрепить файлы")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_more_files_keyboard():
    buttons = [
        [KeyboardButton(text="Да")],
        [KeyboardButton(text="Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_continue_keyboard():
    buttons = [
        [KeyboardButton(text="Продолжить")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_confirmation_keyboard():
    buttons = [
        [KeyboardButton(text="Сохранить")],
        [KeyboardButton(text="Изменить")],
        [KeyboardButton(text="Отменить")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)