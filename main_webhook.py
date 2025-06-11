
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
import uvicorn
import asyncio
import os

API_TOKEN = os.getenv("API_TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище состояний
user_state = {}

# FastAPI app
app = FastAPI()

@dp.message_handler(commands=['start'])
async def launch_consult(message: types.Message):
    user_id = message.chat.id
    user_state[user_id] = {}  # СБРОС состояния при новом заходе

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Я согласен", callback_data="consent_given")
    )
    text = (
        "👋 Добро пожаловать! Этот бот поможет вам записаться на консультацию.\n\n"
        "📌 Мы соблюдаем правила обработки персональных данных (Datenschutz). "
        "Вы можете отозвать согласие в любой момент.\n\n"
        "Пожалуйста, подтвердите согласие, чтобы продолжить:"
    )
    await bot.send_message(message.chat.id, text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == 'consent_given')
async def handle_consent(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "✅ Спасибо! Введите ваше имя:")
    user_state[callback_query.from_user.id] = {"step": "name"}
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler()
async def handle_message(message: types.Message):
    user_id = message.chat.id
    state = user_state.get(user_id, {})

    if state.get("step") == "name":
        user_state[user_id]["name"] = message.text
        user_state[user_id]["step"] = "email"
        await message.answer("✉️ Теперь введите ваш email:")
    elif state.get("step") == "email":
        user_state[user_id]["email"] = message.text
        user_state[user_id]["step"] = "done"
        await message.answer("✅ Спасибо за регистрацию!")
    else:
        await message.answer("Пожалуйста, начните сначала с команды /start.")

# Запуск webhook (в продакшене можно настроить отдельно)
@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())

# FastAPI обёртка
@app.get("/")
async def root():
    return {"status": "бот работает"}
