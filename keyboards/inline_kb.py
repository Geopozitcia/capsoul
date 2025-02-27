from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_time_keyboard():
    times = [
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"
    ]

    buttons = []
    for i in range(0, len(times), 2):  # Разделяем на два столбца
        row = [
            InlineKeyboardButton(text=times[i], callback_data=f"time_{times[i]}"),
            InlineKeyboardButton(text=times[i + 1], callback_data=f"time_{times[i + 1]}")
        ]
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)