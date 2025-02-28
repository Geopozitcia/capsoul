from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, FSInputFile, InputMediaPhoto, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup 
from aiogram.filters.callback_data import CallbackData
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback 


import os
from pathlib import Path
import datetime
import aiosqlite
from pathlib import Path
from keyboards.inline_kb import *
from keyboards.reply_kb import *
from utilits.codes.google_calendar import authenticate_google_calendar, create_calendar_event, is_time_available, find_nearest_available_day, get_events_for_date, WORK_SLOT_EVENT_NAME


router = Router()

DB_NAME = "CAPSOUL.db"


class Form(StatesGroup):
    aim = State()
    experience = State()
    team = State()
    date = State()
    style = State()
    show_solutions = State()  
    final_decision = State()  
    select_date = State()  
    select_time = State()  
    planning = State()  
    more_files = State()  
    ask_question = State()
    add_planning = State()


@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username
    username = f"@{username}" if username else "Не указан"

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, phone FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()

        if not user:
            await db.execute("""
                INSERT OR IGNORE INTO users (id, name, user_name, phone)
                VALUES (?, ?, ?, ?)""", (user_id, name, username, ""))
            await db.commit()

        if not user or not user[1]:
            await message.answer(
                f"Здравствуйте, {name}! Меня зовут Капсула, я ваш умный помощник из студии дизайна интерьеров Capsoul.\n\n"
                f"Для начала запишем ваш номер телефона. Он нужен только для связи с вами.\nОбещаем - спама не будет",
                reply_markup=await contact_keyboard()
            )
        else:
            await message.answer(
                f"Здравствуйте, {name}. Что вы хотите сделать?",
                reply_markup=get_main_menu_keyboard()  # inline кнопки для пользователей которые уже завершили работу с ботом
            )


@router.message(F.content_type == types.ContentType.CONTACT)
async def get_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    user_id = message.from_user.id
    phone = contact.phone_number

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET phone = ? WHERE id = ?""", (phone, user_id))
        await db.commit()

    await message.answer(
        "Спасибо! Ваш номер телефона сохранён.\nДавайте уточним ваши пожелания к дизайн проекту.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.aim)
    await message.answer(
        "Какая основная цель разработки дизайн-проекта и ремонта для вашего объекта?",
        reply_markup=get_aim_keyboard()
    )


@router.message(Form.aim)
async def process_aim(message: types.Message, state: FSMContext):
    aim = message.text
    await state.update_data(aim=aim)

    if aim == "Для личного проживания":
        await message.answer(
            "Здорово! Создавать личное пространство для жизни — это важный и вдохновляющий процесс. Давайте сделаем ваш дом идеальным именно для вас."
        )
    elif aim == "Для инвестиций (аренда, продажа)":
        await message.answer(
            "Отлично! Дизайн для инвестиций — это всегда про стиль, функциональность и универсальность. Мы поможем сделать ваш объект максимально привлекательным для потенциальных клиентов."
        )

    await state.set_state(Form.experience)
    await message.answer(
        "У вас уже был опыт работы с дизайнером?",
        reply_markup=get_experience_keyboard()
    )


@router.message(Form.experience)
async def process_experience(message: types.Message, state: FSMContext):
    experience = message.text
    await state.update_data(experience=experience)

    if experience == "Да, был положительный опыт":
        await message.answer(
            "Прекрасно!\nТогда вы уже знаете, как важно доверять профессионалам. Мы постараемся превзойти ваши ожидания."
        )
    elif experience == "Да, но опыт был неудачным":
        await message.answer(
            "Понимаю, это бывает. Мы сделаем всё, чтобы ваш новый проект прошёл гладко и результат вас порадовал."
        )
    elif experience == "Нет, это мой первый проект с дизайнером":
        await message.answer(
            "Как здорово! Первый проект — это всегда волнительно, но мы будем рядом на каждом этапе, чтобы всё прошло легко и приятно."
        )

    await state.set_state(Form.team)
    await message.answer(
        "Есть ли команда строителей, которым вы можете доверить ремонт?",
        reply_markup=get_team_keyboard()
    )


@router.message(Form.team)
async def process_team(message: types.Message, state: FSMContext):
    team = message.text
    await state.update_data(team=team)

    if team == "Да, есть проверенная команда":
        await message.answer(
            "Это очень хорошо! Слаженная работа с проверенной командой — это уже половина успеха. Мы можем помочь с координацией и рекомендациями!"
        )
    elif team == "Нет, пока ищу специалистов":
        await message.answer(
            "Не переживайте, мы постараемся помочь с этим."
        )
    elif team == "Еще не думал(а) об этом":
        await message.answer(
            "Это нормально! Мы поможем вам разобраться с этим вопросом, когда придёт время. Главное — начать с проекта!"
        )

    await state.set_state(Form.date)
    await message.answer(
        "Когда вы планируете приступить к ремонту?",
        reply_markup=get_date_keyboard()
    )


@router.message(Form.date)
async def process_date(message: types.Message, state: FSMContext):
    date = message.text
    await state.update_data(date=date)

    await message.answer(
        "Все понятно! Учтем это. В любом случае наши проекты создаются в самые короткие сроки."
    )

    minimalism_photo = FSInputFile("utilits/images/minimalism.png")
    modern_classic_photo = FSInputFile("utilits/images/modern_classic.jpg")
    scandi_photo = FSInputFile("utilits/images/sсandi.jpg")

    await message.answer_photo(
        photo=minimalism_photo,
        caption="🎨 Минимализм — для тех, кто ценит простоту, порядок и функциональность."
    )

    await message.answer_photo(
        photo=modern_classic_photo,
        caption="✨ Современная классика — для тех, кто любит элегантность, уют и вечную актуальность."
    )

    await message.answer_photo(
        photo=scandi_photo,
        caption="🪵 Скандинавский стиль — для тех, кто хочет создать светлое, тёплое и комфортное пространство."
    )

    await state.set_state(Form.style)
    await message.answer(
        "Мы хотели бы предложить вам стиль из нашего каталога капсульных интерьеров. Выберите тот, который вам ближе:",
        reply_markup=get_style_keyboard()
    )


@router.message(Form.style)
async def process_style(message: types.Message, state: FSMContext):
    style = message.text
    await state.update_data(style=style)

    data = await state.get_data()
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET
                aim_of_project = ?,
                past_experience = ?,
                team_exist = ?,
                date_of_project = ?,
                design_preferences = ?
            WHERE id = ?""",
            (data['aim'], data['experience'], data['team'], data['date'], data['style'], user_id)
        )
        await db.commit()

    images_path = Path("utilits/images")
    style_images = {
        "Минимализм": ["example_minimalism1.jpg", "example_minimalism2.jpg", "example_minimalism3.jpg"],
        "Современная классика": ["example_modern_classic1.jpg", "example_modern_classic2.jpg", "example_modern_classic3.jpg"],
        "Скандинавский стиль": ["example_scandi1.jpg", "example_scandi2.jpg", "example_scandi3.jpg"]
    }
    descriptions = {
        "Минимализм": "Минимализм — это стиль вне времени для тех, кто ценит порядок, функциональность, чистоту линий и свободу пространства. Ничего лишнего, только комфорт и современный дизайн. Особенно это ценно в нашем современном мире, где много лишних вещей, шума и суеты.",
        "Современная классика": "Современная классика — это сочетание уюта, мягкости и элегантности. Интерьер, который выглядит стильно сегодня и останется актуальным завтра.",
        "Скандинавский стиль": "Скандинавский стиль — это выбор для тех, кто ценит натуральные материалы, функциональность и хорошую простоту. В таком доме тепло и легко дышится."
    }

    media = [InputMediaPhoto(media=FSInputFile(images_path / image_name)) for image_name in style_images[style]]
    await message.answer_media_group(media=media)

    await message.answer(descriptions[style])

    await message.answer(
        "Что вы думаете об этих примерах?",
        reply_markup=get_final_decision_keyboard()
    )
    await state.set_state(Form.final_decision)


@router.message(Form.final_decision)
async def final_decision(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = message.from_user.full_name

    # Находим ближайший доступный день
    service = authenticate_google_calendar()
    nearest_day = find_nearest_available_day(service)
    if nearest_day:
        nearest_day_formatted = datetime.datetime.strptime(nearest_day, "%Y-%m-%d").strftime("%d.%m.%Y")
        await message.answer(
            f"{name}, если хотите узнать, как мы можем адаптировать готовое интерьерное решение именно под вашу планировку и сколько это будет стоить, запишитесь на экспресс-консультацию по видеосвязи с нашим дизайнером.\n"
            f"Это бесплатно и займёт всего 20 минут вашего времени! 😊\n\n"
            f"Ближайший доступный день: {nearest_day_formatted}.\n\n Пожалуйста, выберите дату консультации:",
            reply_markup=await SimpleCalendar(locale="ru_RU").start_calendar()
        )
    else:
        await message.answer(
            "К сожалению, ближайшие 30 дней дизайнер не работает. Пожалуйста, свяжитесь с нами позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Переходим к выбору даты
    await state.set_state(Form.select_date)

@router.callback_query(SimpleCalendarCallback.filter(), Form.select_date)
async def process_calendar(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    selected, date = await SimpleCalendar(locale="ru_RU").process_selection(callback_query, callback_data)
    if selected:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))  # Текущее время в Новосибирске
        if date.date() < now.date() or (date.date() == now.date() and date.time() < now.time()):
            await callback_query.message.answer(
                "Вы выбрали прошедшую дату или время. Пожалуйста, выберите будущую дату.",
                reply_markup=await SimpleCalendar(locale="ru_RU").start_calendar()  # Показываем календарь снова
            )
            return

        await state.update_data(meeting_date=date.strftime("%Y-%m-%d"))  # Сохраняем дату

        await callback_query.message.delete()

        # Проверяем, есть ли рабочие слоты в выбранный день
        service = authenticate_google_calendar()
        events = get_events_for_date(service, date.strftime("%Y-%m-%d"))
        has_work_slots = any(event["summary"] == WORK_SLOT_EVENT_NAME for event in events)

        if not has_work_slots:
            await callback_query.message.answer(
                "В выбранный день дизайнер не работает. Пожалуйста, выберите другой день.",
                reply_markup=await SimpleCalendar(locale="ru_RU").start_calendar()  # Показываем календарь снова
            )
            return

        # Переходим к выбору времени
        await state.set_state(Form.select_time)
        await callback_query.message.answer(
            "Теперь выберите время консультации:",
            reply_markup=get_time_keyboard(date.strftime("%Y-%m-%d"))
        )

# Обработка выбора времени
@router.callback_query(Form.select_time, F.data.startswith("time_"))
async def process_time(callback_query: CallbackQuery, state: FSMContext):
    time = callback_query.data.split("_")[1]  
    await state.update_data(meeting_time=time) 

    data = await state.get_data()
    user_id = callback_query.from_user.id
    meeting_date = data['meeting_date']
    meeting_datetime = f"{meeting_date}T{time}:00+07:00"  # Новосибирское время

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT phone, aim_of_project, past_experience, team_exist, date_of_project, design_preferences FROM users WHERE id = ?", (user_id,))
        user_data_db = await cursor.fetchone()

    user_data = {
        "name": callback_query.from_user.full_name,
        "phone": user_data_db[0] if user_data_db else "Не указан",
        "aim_of_project": user_data_db[1] if user_data_db else "Не указано",
        "past_experience": user_data_db[2] if user_data_db else "Не указано",
        "team_exist": user_data_db[3] if user_data_db else "Не указано",
        "date_of_project": user_data_db[4] if user_data_db else "Не указано",
        "design_preferences": user_data_db[5] if user_data_db else "Не указано",
    }

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET meeting_date = ? WHERE id = ?""",
            (meeting_datetime, user_id)
        )
        await db.commit()

    service = authenticate_google_calendar()
    create_calendar_event(service, user_data, meeting_datetime)

    await callback_query.message.answer(
        f"Мы проведем с вами консультацию {meeting_date} в {time}.\n"
        "\nПока что давайте перейдем к следующему шагу:", 
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(Form.planning)
    await callback_query.message.answer(
        "Пожалуйста, прикрепите файл с планировкой (это может быть фото, скан или PDF).\n"
        "\nЕсли у вас нет плана под рукой, просто отправьте схематичный чертёж — этого будет достаточно для первого этапа. 😊",
        reply_markup=get_planning_keyboard()
    )


@router.message(Form.planning, F.text == "Нет планировки")
async def no_planning(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    name = message.from_user.full_name
    meeting_date = data.get("meeting_date")
    meeting_time = data.get("meeting_time")

    meeting_date_formatted = datetime.datetime.strptime(meeting_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    meeting_time_formatted = meeting_time

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET planning_file = ? WHERE id = ?""",
            ("Нет планировки", user_id)
        )
        await db.commit()

    await message.answer(
        "Если у вас сейчас нет планировки, ничего страшного! Пожалуйста, постарайтесь найти её к моменту нашей консультации. "
        "\nПланировка поможет нам лучше понять ваш запрос и сразу предложить подходящее решение. Если у вас не получится найти план, "
        "мы всё равно сможем обсудить основные моменты на созвоне. 😊"
    )

    await message.answer(
        f"Давайте подведем итоги...\n\n"
        f"{name}, вы записаны на экспресс-консультацию с ведущим дизайнером Алевтиной.\n"
        f"\nДата консультации {meeting_date_formatted}, в {meeting_time_formatted}.\n\n"
        f"Созвон пройдёт через Яндекс Телемост. Вам не нужно ничего\n"
        f"устанавливать — просто перейдите по ссылке в указанное время:"
        f"\n\n[ССЫЛКА].\n\n"
        f"Если у вас появятся вопросы до консультации, вы можете оставить сообщение в соответствующей вкладке. До встречи! 💋",
        reply_markup=get_continue_keyboard()
    )
    await state.clear()


@router.message(Form.planning, F.text == "Прикрепить файлы")
async def attach_files(message: types.Message, state: FSMContext):
    await message.answer(
        "Ждем ваши файлы 👀",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.more_files)

@router.message(Form.more_files, F.document | F.photo)
async def save_file(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name  
    else:
        file_id = message.photo[-1].file_id
        file_name = f"photo_{file_id}.jpg" 

    file = await message.bot.get_file(file_id)
    file_path = file.file_path

# на каждого гражданина папочка отдельная

    user_folder = Path(f"storage/user_files_{user_id}")
    user_folder.mkdir(parents=True, exist_ok=True)

    await message.bot.download_file(file_path, user_folder / file_name)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET planning_file = ? WHERE id = ?""",
            (f"user_files_{user_id}", user_id)
        )
        await db.commit()

    await message.answer(
        "Файл успешно сохранён. Хотите ли вы прикрепить ещё файлы?",
        reply_markup=get_more_files_keyboard()
    )

@router.message(Form.more_files, F.text == "Да")
async def more_files_yes(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, отправьте следующий файл.",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(Form.more_files, F.text == "Нет")
async def more_files_no(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    name = message.from_user.full_name

    meeting_date = data.get("meeting_date")
    if meeting_date:
        meeting_date_formatted = datetime.datetime.strptime(meeting_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    else:
        meeting_date_formatted = "не указана"

    meeting_time = data.get("meeting_time")
    if meeting_time:
        meeting_time_formatted = meeting_time
    else:
        meeting_time_formatted = "не указано"

    await message.answer(
        f"Давайте подведем итоги...\n\n"
        f"{name}, вы записаны на экспресс-консультацию с ведущим дизайнером Алевтина.\n"
        f"Дата консультации {meeting_date_formatted}, в {meeting_time_formatted}.\n"
        f"Созвон пройдёт через Яндекс Телемост. Вам не нужно ничего\n"
        f"устанавливать — просто перейдите по ссылке в указанное время:"
        f"\n\n[ССЫЛКА].\n\n"
        f"Если у вас появятся вопросы до консультации, вы можете оставить сообщение в соответствующей вкладке. До встречи! 💋",
        reply_markup=get_continue_keyboard()
    )
    await state.clear()

    
@router.message(F.text == "Продолжить")
async def continue_handler(message: types.Message, state: FSMContext):
    await start_handler(message, state)  

@router.callback_query(F.data == "my_consultation")
async def my_consultation(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    name = callback_query.from_user.full_name

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT meeting_date, phone FROM users WHERE id = ?", (user_id,))
        user_data = await cursor.fetchone()

    if user_data and user_data[0]:
        meeting_datetime = user_data[0]
        meeting_date = datetime.datetime.fromisoformat(meeting_datetime).strftime("%d.%m.%Y")
        meeting_time = datetime.datetime.fromisoformat(meeting_datetime).strftime("%H:%M")

        await callback_query.message.answer(
            f"{name}, вы записаны на экспресс-консультацию с ведущим дизайнером Алевтина.\n"
            f"Дата консультации {meeting_date}, в {meeting_time}.\n\n"
            f"Созвон пройдёт через Яндекс Телемост. Вам не нужно ничего\n"
            f"устанавливать — просто перейдите по ссылке в указанное время:"
            f"\n\n[ССЫЛКА].\n\n"
            f"Если у вас появятся вопросы до консультации, вы можете оставить сообщение в соответствующей вкладке. До встречи! 💋"
        )
    else:
        await callback_query.message.answer("У вас нет активной записи на консультацию.")

    await callback_query.message.answer(
        f"Здравствуйте, {name}. Что вы хотите сделать?",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "add_planning")
async def add_planning(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Пожалуйста, отправьте файл с планировкой.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.add_planning)  

@router.callback_query(F.data == "ask_question")
async def ask_question(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Пожалуйста, напишите ваш вопрос:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.ask_question)

@router.message(Form.ask_question)
async def process_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username
    username = f"@{username}" if username else "Не указан"

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT phone FROM users WHERE id = ?", (user_id,))
        phone = await cursor.fetchone()
        phone = phone[0] if phone else "Не указан"

    # Пересылаем вопрос в чат
    try:
        await message.bot.send_message(
            chat_id=-1002356191665,  # Используем ID чата с префиксом -100 для супергрупп
            text=f"Пользователь {name} спрашивает: {message.text}\n"
                 f"Телефон: {phone}\n"
                 f"Никнейм пользователя: {username}"
        )
        await message.answer("Ваш вопрос отправлен. Мы свяжемся с вами в ближайшее время.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при отправке вопроса: {e}")

    await message.answer(
        f"Здравствуйте, {name}. Что вы хотите сделать?",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Form.add_planning, F.document | F.photo)
async def save_file_from_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name  
    else:
        file_id = message.photo[-1].file_id
        file_name = f"photo_{file_id}.jpg"  

    file = await message.bot.get_file(file_id)
    file_path = file.file_path

    user_folder = Path(f"storage/user_files_{user_id}")
    user_folder.mkdir(parents=True, exist_ok=True)

    await message.bot.download_file(file_path, user_folder / file_name)

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET planning_file = ? WHERE id = ?""",
            (f"user_files_{user_id}", user_id)
        )
        await db.commit()

    await message.answer(
        "Файл успешно сохранён. Хотите ли вы прикрепить ещё файлы?",
        reply_markup=get_more_files_keyboard()
    )


@router.message(Form.add_planning, F.text == "Нет")
async def more_files_no_from_menu(message: types.Message, state: FSMContext):
    await message.answer(
        "Спасибо, ваши файлы у нас.",
        reply_markup=ReplyKeyboardRemove()  
    )
    await message.answer(
        f"Здравствуйте, {message.from_user.full_name}. Что вы хотите сделать?",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()