import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Путь к файлу ключа сервисного аккаунта
SERVICE_ACCOUNT_FILE = "utilits/codes/key.json"

# Идентификатор календаря
CALENDAR_ID = "68b0899d698e09b08ca7bcbc1e02e699778cc6c65c04b747d138aecade045308@group.calendar.google.com"

# Настройка временной зоны для Новосибирска (+7 часов от GMT)
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

    for event in events:
        event_start = event["start"].get("dateTime", event["start"].get("date"))
        event_end = event["end"].get("dateTime", event["end"].get("date"))

        # Проверяем, пересекается ли выбранное время с существующими событиями
        if (event_start < target_end) and (event_end > target_start):
            if event["summary"] == WORK_SLOT_EVENT_NAME:
                return True  # Время доступно для записи
            else:
                return False  # Время занято другой консультацией

    return False  # Нет рабочего слота в это время


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
            "dateTime": (datetime.datetime.fromisoformat(meeting_datetime) + datetime.timedelta(hours=1)).isoformat(),
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