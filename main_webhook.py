
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook
from fastapi import FastAPI, Request
from aiogram.dispatcher.filters import Text
import os

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL") + WEBHOOK_PATH

bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
Bot.set_current(bot)
dp = Dispatcher(bot)
app = FastAPI()

user_state = {}
user_data = {}

@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return {"ok": True}

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    user_state.pop(user_id, None)
    user_data.pop(user_id, None)
    user_state[user_id] = 'name'
    await message.answer("👋 Добро пожаловать! Введите, пожалуйста, ваше имя:")

@dp.message_handler(lambda message: user_state.get(message.from_user.id) == 'name')
async def handle_name(message: types.Message):
    name = message.text.strip()
    user_id = message.from_user.id
    if len(name) < 3:
        await bot.send_message(user_id, "❌ Некорректное имя. Введите ещё раз (минимум 3 символа):")
        return
    user_data[user_id] = {"name": name}
    user_state[user_id] = 'topics'
    await bot.send_message(user_id, "✅ Имя принято.")
    await send_topic_selection(user_id)

async def send_topic_selection(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    topics = ["Консультация по страховке", "Инвестиции", "Пенсия", "Кредитование", "Gewerbe", "Имущество"]
    buttons = [InlineKeyboardButton(text=topic, callback_data=f"topic_{topic}") for topic in topics]
    kb.add(*buttons)
    await bot.send_message(user_id, "📌 Выберите одну или несколько тем:", reply_markup=kb)
