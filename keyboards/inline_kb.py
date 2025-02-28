import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utilits.codes.google_calendar import authenticate_google_calendar, create_calendar_event, is_time_available, find_nearest_available_day, get_events_for_date, WORK_SLOT_EVENT_NAME


def get_time_keyboard(date):
    """Создает клавиатуру с доступным временем."""
    service = authenticate_google_calendar()
    events = get_events_for_date(service, date)

    # Все возможные временные слоты
    all_times = [
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"
    ]

    # Фильтруем доступное время
    available_times = []
    for time in all_times:
        target_start = f"{date}T{time}:00+07:00"
        target_end = (datetime.datetime.fromisoformat(target_start) + datetime.timedelta(minutes=30)).isoformat()

        is_available = True
        for event in events:
            event_start = event["start"].get("dateTime", event["start"].get("date"))
            event_end = event["end"].get("dateTime", event["end"].get("date"))

            # Проверяем, пересекается ли выбранное время с существующими событиями
            if (event_start < target_end) and (event_end > target_start):
                if event["summary"] != WORK_SLOT_EVENT_NAME:
                    is_available = False
                    break

        # Проверяем, есть ли рабочий слот в это время
        if is_available:
            for event in events:
                event_start = event["start"].get("dateTime", event["start"].get("date"))
                event_end = event["end"].get("dateTime", event["end"].get("date"))
                if (event_start <= target_start) and (event_end >= target_end) and (event["summary"] == WORK_SLOT_EVENT_NAME):
                    available_times.append(time)
                    break

    # Создаем кнопки для доступного времени
    buttons = []
    for i in range(0, len(available_times), 2):  # Разделяем на два столбца
        row = [
            InlineKeyboardButton(text=available_times[i], callback_data=f"time_{available_times[i]}"),
            InlineKeyboardButton(text=available_times[i + 1], callback_data=f"time_{available_times[i + 1]}")
        ] if i + 1 < len(available_times) else [
            InlineKeyboardButton(text=available_times[i], callback_data=f"time_{available_times[i]}")
        ]
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)