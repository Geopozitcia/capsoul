import os
import asyncio
import re
from aiogram.enums import ParseMode
from aiogram import Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.types import InputMediaPhoto
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
from core.keyboards.inline import show_basket_inline, basket_inl
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request


class basketstate(StatesGroup):
    basket_quantity=State()
    delivery_date=State()


########### Обработка нажатия на кнопку "Добавить в корзину"
async def add_to_basket(call: CallbackQuery, state: FSMContext):
    product_id = call.data.split('_')[1]
    user_id = call.from_user.id

    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM basket WHERE user_id=? AND product_id=?", (user_id, product_id))
        existing_item = cur.fetchone()

        if existing_item:
            cur.execute("UPDATE basket SET quantity = quantity + 1 WHERE user_id=? AND product_id=?", (user_id, product_id))
        else:
            cur.execute("INSERT INTO basket (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, 1))

        con.commit()

    show_basket_inline = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='🛒 Моя корзина', callback_data="show_basket")]]
    )

    message = await call.message.answer("Товар добавлен в корзину.", reply_markup=show_basket_inline)
    
    # Сохраняем ID сообщения "Товар добавлен в корзину"
    await state.update_data(add_to_basket_message_id=message.message_id)
    await call.answer()

async def process_quantity(message: Message, state: FSMContext):
    quantity = message.text
    if not quantity.isdigit() or int(quantity) <= 0:
        await message.answer("Пожалуйста, введите положительное число.", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    product_id = data.get("product_id")
    user_id = message.from_user.id

    try:
        with sq.connect('PINCODE.db') as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO basket (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, int(quantity))
            )
            con.commit()

        # От 6 февраял 
        await state.clear()

        # От 6 февраля
        show_basket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🛒 Моя корзина', callback_data="show_basket")]
        ])
        await message.answer("Товар добавлен в корзину", reply_markup=show_basket_keyboard)

    except Exception as e:
        await message.answer("Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте позже.")
        print(f"Ошибка при добавлении товара в корзину: {e}")
#############


############ Отображение корзины
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

class basket_in(StatesGroup):
    basket = State()

def convert_price(price_str):
    if not price_str:
        return 0.0

    cleaned_price = re.sub(r'[^\d,\.]', '', price_str).replace(',', '.')

    try:
        return float(cleaned_price)
    except ValueError:
        print(f"Ошибка при преобразовании цены: {price_str} -> {cleaned_price}")  # Логирование ошибки
        return 0.0
    
async def check_basket_validity(call: CallbackQuery, state: FSMContext): # для багфикса
    user_id = call.from_user.id

    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("SELECT product_id FROM basket WHERE user_id=?", (user_id,))
        basket_items = cur.fetchall()

        invalid_items = []
        for (product_id,) in basket_items:
            cur.execute("SELECT id FROM tovari WHERE id=?", (product_id,))
            if not cur.fetchone():
                invalid_items.append(product_id)

        if invalid_items:
            # Удаляем несуществующие товары из корзины
            for product_id in invalid_items:
                cur.execute("DELETE FROM basket WHERE user_id=? AND product_id=?", (user_id, product_id))
            con.commit()

            # Отправляем уведомление пользователю
            await call.message.answer(
                "⚠️ Некоторые товары были удалены из магазина и убраны из вашей корзины. "
                "Пожалуйста, пересмотрите ваш заказ."
            )

            return False  
        return True  

# Функция для отображения корзины
async def show_basket_item(call: CallbackQuery, state: FSMContext, index: int = 0):
    user_id = call.from_user.id

    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM basket WHERE user_id=?", (user_id,))
        basket_items = cur.fetchall()

        if not basket_items:
            await call.message.answer("🛒 Ваша корзина пуста.")
            return

        # Проверяем актуальность товаров в корзине
        invalid_items = await check_basket_validity(user_id)
        if invalid_items:
            warning_message = "⚠️ Некоторые товары изменились или стали недоступны:\n\n"
            for item in invalid_items:
                warning_message += f"❌ {item}\n"
            warning_message += "\nПожалуйста, обновите корзину."
            await call.message.answer(warning_message)
            return

        # Удаляем сообщение "Товар добавлен в корзину", если оно есть
        data = await state.get_data()
        add_to_basket_message_id = data.get("add_to_basket_message_id")

        if add_to_basket_message_id:
            try:
                await call.bot.delete_message(chat_id=call.message.chat.id, message_id=add_to_basket_message_id)
                await state.update_data(add_to_basket_message_id=None)  # Очищаем ID сообщения
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")

        item = basket_items[index]
        product_id = item[2]
        quantity = item[3]
        total_items = len(basket_items)

        await state.set_state(basket_in.basket)

        cur.execute("SELECT * FROM tovari WHERE id=?", (product_id,))
        product = cur.fetchone()

        if not product:
            await call.message.answer(f"❌ Товар с ID {product_id} не найден.")
            return

        price_str = product[8]  
        price = convert_price(price_str)
        item_total = price * quantity

        try:
            photo_path = f"images/{product_id}.jpg"
            caption = (f"<b>{product[1]}</b>\n"
                       f"<i>Описание</i>: {product[2]}\n\n"
                       f"🔢 Количество: {quantity}\n"
                       f"📌 Товар {index + 1} из {total_items}")
            
            data = await state.get_data()
            photo_message_id = data.get("photo_message_id")
            basket_message_id = data.get("basket_message_id")

            if photo_message_id:
                media = InputMediaPhoto(
                    media=FSInputFile(photo_path),
                    caption=caption,
                    parse_mode="HTML"
                )
                await call.bot.edit_message_media(
                    chat_id=call.message.chat.id,
                    message_id=photo_message_id,
                    media=media,
                    reply_markup=basket_inl(index, product_id, total_items),
                )
            else:
                photo_message = await call.message.answer_photo(
                    photo=FSInputFile(photo_path),
                    caption=caption,
                    reply_markup=basket_inl(index, product_id, total_items),
                    parse_mode="HTML"
                )
                await state.update_data(photo_message_id=photo_message.message_id)

        except Exception as e:
            pass

        # Составляем итоговое сообщение о корзине
        basket_summary = "🛒 <b>Содержимое корзины:</b>\n\n"
        total_price = 0

        for item in basket_items:
            product_id = item[2]
            quantity = item[3]

            cur.execute("SELECT * FROM tovari WHERE id=?", (product_id,))
            product = cur.fetchone()

            if not product:
                continue

            price_str = product[8]
            price = convert_price(price_str)
            item_total = price * quantity
            total_price += item_total

            basket_summary += f"• {product[1]} - {quantity} шт.\n"

        basket_summary += f"\n💰 <b>Общая стоимость:</b> {total_price:.2f} ₽"

        if basket_message_id:
            await call.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=basket_message_id,
                text=basket_summary,
                parse_mode="HTML"
            )
        else:
            basket_message = await call.message.answer(basket_summary, parse_mode="HTML")
            await state.update_data(basket_message_id=basket_message.message_id)

        await state.update_data(current_index=index, basket_items=basket_items)

############## Далее и Назад


async def next_item(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    basket_items = data.get("basket_items", [])

    next_index = current_index + 1

    if next_index >= len(basket_items):
        next_index = 0

    await state.update_data(current_index=next_index)
    await show_basket_item(call, state, next_index)
    await call.answer()

async def previous_item(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    basket_items = data.get("basket_items", [])
    previous_index = current_index - 1

    if previous_index < 0:
        previous_index = len(basket_items) - 1

    await state.update_data(current_index=previous_index)
    await show_basket_item(call, state, previous_index)
    await call.answer()
########

############# Обработка действий в корзине

async def remove_from_basket(call: CallbackQuery, state: FSMContext):
    product_id = call.data.split('_')[1]
    user_id = call.from_user.id

    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("DELETE FROM basket WHERE user_id=? AND product_id=?", (user_id, product_id))
        con.commit()
        cur.execute("SELECT * FROM basket WHERE user_id=?", (user_id,))
        basket_items = cur.fetchall()

    if basket_items:
        await state.update_data(basket_items=basket_items, current_index=0)
        await show_basket_item(call, state, index=0)
    else:
        data = await state.get_data()
        photo_message_id = data.get("photo_message_id")
        basket_message_id = data.get("basket_message_id")

        # Удаление сообщений, если они существуют
        if photo_message_id:
            await call.bot.delete_message(chat_id=call.message.chat.id, message_id=photo_message_id)
        if basket_message_id:
            await call.bot.delete_message(chat_id=call.message.chat.id, message_id=basket_message_id)

        # От 6 февраля
        await state.clear()

        await call.answer()
        await call.message.answer("Ваша корзина пуста.")

async def increase_quantity(call: CallbackQuery, state: FSMContext):
    product_id = call.data.split('_')[1]
    user_id = call.from_user.id

    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("UPDATE basket SET quantity = quantity + 1 WHERE user_id=? AND product_id=?", (user_id, product_id))
        con.commit()

    data = await state.get_data()
    current_index = data.get("current_index", 0)
    
    await show_basket_item(call, state, current_index)
    await call.answer("Количество увеличено на 1")

async def decrease_quantity(call: CallbackQuery, state: FSMContext):
    product_id = call.data.split('_')[1]
    user_id = call.from_user.id

    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("SELECT quantity FROM basket WHERE user_id=? AND product_id=?", (user_id, product_id))
        row = cur.fetchone()

        if row is None:
            await call.answer("Ошибка: товар не найден в корзине.")
            return
        
        current_quantity = row[0]

        if current_quantity > 1:
            # Уменьшаем количество на 1
            cur.execute("UPDATE basket SET quantity = quantity - 1 WHERE user_id=? AND product_id=?", (user_id, product_id))
            con.commit()
            data = await state.get_data()
            current_index = data.get("current_index", 0)
            await show_basket_item(call, state, current_index)
            await call.answer("Количество уменьшено на 1")
        else:
            # Если количество = 1, удаляем товар
            await remove_from_basket(call, state)

from core.keyboards.replykeyboard import kb, start_kb



class BasketState(StatesGroup): # стадии
    delivery_date = State()
    delivery_time = State()

async def checkout(call: CallbackQuery, state: FSMContext):
    is_valid = await check_basket_validity(call, state)
    if not is_valid:
        return  
    await call.message.answer("Выберите дату доставки:",
                              reply_markup=await SimpleCalendar(locale='ru_RU.utf8').start_calendar())
    await state.set_state(BasketState.delivery_date)  # Исправлено
    await call.answer()


async def show_delivery_time_keyboard(callback_query, state): # утилита для клавиатуры
    time_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="с 9 до 12", callback_data="time_9_12")],
        [InlineKeyboardButton(text="с 14 до 18", callback_data="time_14_18")],
        [InlineKeyboardButton(text="Отменить заказ", callback_data="cancel_order")],  # Добавляем кнопку отмены
    ])
    
    await callback_query.message.answer(
        "Выберите время доставки:",
        reply_markup=time_keyboard
    )
    await state.set_state(BasketState.delivery_time)


async def process_delivery_date(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    is_valid = await check_basket_validity(callback_query, state)
    if not is_valid:
        return  

    selected, date = await SimpleCalendar(locale='ru_RU.utf8').process_selection(callback_query, callback_data)
    if selected:
        if date > datetime.now() + timedelta(days=90):
            await callback_query.message.answer(
                "Срок доставки должен быть менее 90 дней. Пожалуйста, выберите другую дату:",
                reply_markup=await SimpleCalendar(locale='ru_RU.utf8').start_calendar()
            )
            return
        elif date <= datetime.now():
            await callback_query.message.answer(
                "Заказ можно оформить только на завтра, или позже. Пожалуйста, выберите другую дату:",
                reply_markup=await SimpleCalendar(locale='ru_RU.utf8').start_calendar()
            )
            return
        
        await callback_query.message.delete()

        delivery_date = date.strftime("%d.%m.%Y")
        await state.update_data(delivery_date=delivery_date)
        await show_delivery_time_keyboard(callback_query, state)

async def process_delivery_time(callback_query: CallbackQuery, state: FSMContext):
    is_valid = await check_basket_validity(callback_query, state)
    if not is_valid:
        return  

    time_choice = None
    if callback_query.data == "time_9_12":
        time_choice = "с 9 до 12"
    elif callback_query.data == "time_14_18":
        time_choice = "с 14 до 18"
    
    delivery_date = await state.get_data()
    delivery_date = delivery_date.get('delivery_date')
    full_delivery_info = f"{delivery_date} {time_choice}"
    user_id = callback_query.from_user.id
    
    with sq.connect('PINCODE.db') as con:
        cur = con.cursor()
        cur.execute("SELECT id_zakaza FROM zakazi")
        ids = cur.fetchall()
        new_id = max([int(id[0]) for id in ids]) + 1 if ids else 1

        cur.execute("SELECT * FROM basket WHERE user_id=?", (user_id,))
        basket_items = cur.fetchall()
        for item in basket_items:
            product_id, quantity = item[2], item[3]
            cur.execute("SELECT id_prodavca FROM tovari WHERE id=?", (product_id,))
            seller_id = cur.fetchone()
            seller_id = seller_id[0] if seller_id else None

            cur.execute("""
                INSERT INTO zakazi (id_zakaza, order_by, tovar, order_to, kol, date, zakorpred) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (new_id, user_id, product_id, seller_id, quantity, full_delivery_info, "заказ через корзину"))

        cur.execute("DELETE FROM basket WHERE user_id=?", (user_id,))
        con.commit()
        cur.execute("SELECT * FROM zakazi")
        zakazi_data = cur.fetchall()
        formatted_data = [list(row) for row in zakazi_data]
        send_to_google_sheets(formatted_data)

    main_menu_button = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Главное меню", callback_data="mainmenu")]
    ])
    await callback_query.answer()
    await callback_query.message.answer(
        f'Ваш заказ на {full_delivery_info}, оформлен. Он уже у нас, и скоро будет рассмотрен. Спасибо!',
        reply_markup=main_menu_button
    )
    await state.clear()



async def cancel_order(callback_query: CallbackQuery, state: FSMContext): # утилита для отмены товара
    await state.clear()

    main_menu_button = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Главное меню", callback_data="mainmenu")] 
    ])

    await callback_query.message.answer(
        "Ваш заказ был отменен. Пожалуйста, выберите дальнейшие действия.",
        reply_markup=main_menu_button
    )

    ######################## утилиты для отправки в google shits
def connect_to_google_sheets():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file('cred.json', scopes=scope)  # credentials with scopes
    client = gspread.authorize(credentials)
    sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/15AVrAsZVs1ic0JsNqBJuzC1FQvU9pIKXANBZ9iXxYy0').worksheet("Тестирование корзины")
    return sheet

# Функция для добавления данных в Google Sheets
def send_to_google_sheets(data):
    sheet = connect_to_google_sheets()
    sheet.append_rows(data, value_input_option='RAW')  


