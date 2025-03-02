import datetime
import logging
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv


load_dotenv()
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
CALENDAR_ID = "68b0899d698e09b08ca7bcbc1e02e699778cc6c65c04b747d138aecade045308@group.calendar.google.com"
TIME_ZONE = "Asia/Novosibirsk"

# Название события для рабочих слотов
WORK_SLOT_EVENT_NAME = "Время для консультаций"


def authenticate_google_calendar():
    """Аутентификация через сервисный аккаунт."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=creds)


def get_events_for_date(service, date):
    """Получает все события на указанную дату."""
    start_of_day = f"{date}T00:00:00+07:00"
    end_of_day = f"{date}T23:59:59+07:00"

    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


def is_time_available(service, date, time):
    """Проверяет, доступно ли время для записи."""
    events = get_events_for_date(service, date)
    target_start = f"{date}T{time}:00+07:00"
    target_end = (datetime.datetime.fromisoformat(target_start) + datetime.timedelta(hours=1)).isoformat()

    # Проверяем, есть ли рабочий слот, который покрывает выбранное время
    has_work_slot = False
    for event in events:
        event_start = event["start"].get("dateTime", event["start"].get("date"))
        event_end = event["end"].get("dateTime", event["end"].get("date"))

        if event["summary"] == WORK_SLOT_EVENT_NAME:
            # Проверяем, полностью ли выбранное время находится внутри рабочего слота
            if event_start <= target_start and event_end >= target_end:
                has_work_slot = True
                break

    if not has_work_slot:
        return False  # Нет рабочего слота, покрывающего выбранное время

    # Проверяем, нет ли других событий, которые пересекаются с выбранным временем
    for event in events:
        event_start = event["start"].get("dateTime", event["start"].get("date"))
        event_end = event["end"].get("dateTime", event["end"].get("date"))

        if event["summary"] != WORK_SLOT_EVENT_NAME:
            # Проверяем, пересекается ли выбранное время с другими событиями
            if (event_start < target_end) and (event_end > target_start):
                return False  # Время занято другим событием

    return True  # Время доступно для записи

def find_nearest_available_day(service):
    """Находит ближайший день с рабочими слотами."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))  # Текущее время в Новосибирске
    for delta in range(0, 30):  # Проверяем ближайшие 30 дней
        target_date = (now + datetime.timedelta(days=delta)).strftime("%Y-%m-%d")
        events = get_events_for_date(service, target_date)
        if any(event["summary"] == WORK_SLOT_EVENT_NAME for event in events):
            return target_date
    return None


def create_calendar_event(service, user_data, meeting_datetime):
    """Создание события в Google Calendar."""
    event = {
        "summary": f"Консультация с {user_data['name']}",
        "location": "Онлайн",
        "description": (
            f"Имя: {user_data['name']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Цель проекта: {user_data['aim_of_project']}\n"
            f"Опыт: {user_data['past_experience']}\n"
            f"Команда: {user_data['team_exist']}\n"
            f"Дата проекта: {user_data['date_of_project']}\n"
            f"Предпочтения: {user_data['design_preferences']}"
        ),
        "start": {
            "dateTime": meeting_datetime,
            "timeZone": TIME_ZONE,
        },
        "end": {
            "dateTime": (datetime.datetime.fromisoformat(meeting_datetime) + datetime.timedelta(minutes=30)).isoformat(),
            "timeZone": TIME_ZONE,
        },
        "reminders": {
            "useDefault": True,
        },
    }

    try:
        event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event
        ).execute()
        print(f"Событие создано: {event.get('htmlLink')}")
        return event
    except HttpError as error:
        print(f"Ошибка при создании события: {error}")
        return None
    
def get_available_times_for_date(service, date):
    """Возвращает список доступного времени на выбранный день."""
    events = get_events_for_date(service, date)

    all_times = [
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"
    ]

    available_times = []
    current_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))  # Текущее время в Новосибирске

    for time in all_times:
        target_start = f"{date}T{time}:00+07:00"
        target_start_dt = datetime.datetime.fromisoformat(target_start)

        # Проверяем, не прошло ли уже это время
        if target_start_dt < current_time:
            continue  # Пропускаем прошедшее время

        target_end = (target_start_dt + datetime.timedelta(minutes=30)).isoformat()

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

    return available_times