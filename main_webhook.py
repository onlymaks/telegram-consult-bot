from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from fastapi import FastAPI
import logging
import os

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "your_bot_token_here")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

user_state = {}
callback_data = CallbackData("action", "value")

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    if message.get_args() == "consult":
        await launch_consult(message)
    else:
        await message.answer("Привет! Отправь команду /start?start=consult чтобы записаться.")

async def launch_consult(message):
    user_id = message.chat.id
    user_state[user_id] = {}  # сброс состояния пользователя при старте

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

@dp.callback_query_handler(lambda c: c.data == "consent_given")
async def consent_given(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "name"
    await bot.send_message(user_id, "Как вас зовут?")

@dp.message_handler(lambda message: user_state.get(message.chat.id, {}).get("step") == "name")
async def process_name(message: types.Message):
    user_id = message.chat.id
    user_state[user_id]["name"] = message.text
    user_state[user_id]["step"] = "email"
    await message.answer("Введите ваш Email:")

@dp.message_handler(lambda message: user_state.get(message.chat.id, {}).get("step") == "email")
async def process_email(message: types.Message):
    user_id = message.chat.id
    user_state[user_id]["email"] = message.text
    user_state[user_id]["step"] = "done"
    await message.answer("Спасибо, вы успешно записались на консультацию!")

# webhook route for Render/FastAPI compatibility
@app.post("/webhook/{token}")
async def webhook(token: str, update: dict):
    if token == API_TOKEN:
        telegram_update = types.Update.to_object(update)
        await dp.process_update(telegram_update)
    return {"ok": True}