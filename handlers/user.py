from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.reply_kb import (
    contact_keyboard,
    get_aim_keyboard,
    get_experience_keyboard,
    get_team_keyboard,
    get_date_keyboard,
    get_style_keyboard
)
import aiosqlite

router = Router()

DB_NAME = "CAPSOUL.db"


class Form(StatesGroup):
    aim = State()
    experience = State()
    team = State()
    date = State()
    style = State()


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
                reply_markup=ReplyKeyboardRemove()
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

    if aim == "для себя":
        await message.answer(
            "Отлично! Дизайн для инвестиций — это всегда про стиль, функциональность и универсальность. Мы поможем сделать ваш объект максимально привлекательным для потенциальных клиентов."
        )
    else:
        await message.answer(
            "Здорово! Создавать личное пространство для жизни — это важный и вдохновляющий процесс. Давайте сделаем ваш дом идеальным именно для вас."
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
            "Прекрасно! Тогда вы уже знаете, как важно доверять профессионалам. Мы постараемся превзойти ваши ожидания."
        )
    elif experience == "Да, но опыт был неудачным":
        await message.answer(
            "Понимаю, это бывает. Мы сделаем всё, чтобы ваш новый проект прошёл гладко и результат вас порадовал."
        )
    else:
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

    if team == "да":
        await message.answer(
            "Это очень хорошо) Слаженная работа с проверенной командой — это уже половина успеха. Мы можем помочь с координацией и рекомендациями!"
        )
    elif team == "нет":
        await message.answer(
            "Не переживайте, мы постараемся помочь с этим."
        )
    else:
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

    await state.set_state(Form.style)
    await message.answer(
        "Мы хотели бы предложить вам стиль из нашего каталога капсульных интерьеров. Выберите тот, который вам ближе.",
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

    await message.answer(
        "Спасибо за ответы! Ваши предпочтения сохранены. Мы свяжемся с вами в ближайшее время.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()