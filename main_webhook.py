
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
import os

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

app = FastAPI()

user_state = {}

@app.post("/webhook/{token}")
async def webhook_handler(token: str, request: Request):
    if token != API_TOKEN:
        return {"status": "unauthorized"}

    update = types.Update(**await request.json())
    await dp.process_update(update)
    return {"status": "ok"}

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"step": "name"}
    await message.answer("👋 Привет! Введи своё имя:")

@dp.message_handler(lambda message: user_state.get(message.from_user.id, {}).get("step") == "name")
async def ask_email(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["name"] = message.text
    user_state[user_id]["step"] = "email"
    await message.answer("📧 Введи свой Email:")

@dp.message_handler(lambda message: user_state.get(message.from_user.id, {}).get("step") == "email")
async def ask_consent(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["email"] = message.text
    user_state[user_id]["step"] = "consent"

    consent_text = (
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.
"
        "Ich kann diese jederzeit unter email widerrufen.

"
        "Согласие на обработку и хранение персональных данных.
"
        "Мне известно, что я могу в любой момент отозвать это согласие по email."
    )
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Я согласен", callback_data="consent_accepted")
    )
    await message.answer(consent_text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "consent_accepted")
async def ask_comment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]["step"] = "comment"
    await bot.send_message(user_id, "✏️ Напиши комментарий:")
