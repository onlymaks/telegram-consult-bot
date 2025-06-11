
import logging
import re
import gspread
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from fastapi import FastAPI, Request
from oauth2client.service_account import ServiceAccountCredentials

API_TOKEN = "PLACEHOLDER"
GOOGLE_SHEET_NAME = "Заявки консультации"
GOOGLE_SHEET_COLUMNS = ["ID", "Имя", "Темы", "Телефон", "Email", "Комментарий", "Согласие", "Обработано"]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1

user_state = {}

@app.post("/webhook/{token}")
async def webhook_handler(request: Request, token: str):
    update = types.Update(**(await request.json()))
    await dp.process_update(update)
    return {"status": "ok"}

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"step": "name"}
    await bot.send_message(user_id, "👋 Привет! Введите ваше имя:")

@dp.message_handler(lambda message: message.text)
async def process_input(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    if user_id not in user_state:
        user_state[user_id] = {"step": "name"}

    step = user_state[user_id]["step"]

    if step == "name":
        if len(text) < 3:
            await message.answer("❗ Некорректное имя. Введите ещё раз.")
            return
        user_state[user_id]["name"] = text
        user_state[user_id]["step"] = "topics"
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📊 Финансовое планирование", callback_data="topic:Финансовое планирование"),
            InlineKeyboardButton("🏡 Ипотека", callback_data="topic:Ипотека"),
            InlineKeyboardButton("💼 Страхование", callback_data="topic:Страхование"),
            InlineKeyboardButton("🇩🇪 Переезд в Германию", callback_data="topic:Переезд"),
            InlineKeyboardButton("✅ Готово", callback_data="done_topics")
        )
        await message.answer("Выберите интересующие темы (можно несколько):", reply_markup=keyboard)

    elif step == "phone":
        if not text.startswith("+49") or not re.match(r"^\+49\d{7,}$", text):
            await message.answer("❗ Неверный формат телефона. Введите в формате +49...")
            return
        user_state[user_id]["phone"] = text
        user_state[user_id]["step"] = "email"
        await message.answer("✉️ Введите ваш Email:")

    elif step == "email":
        if not re.match(r"[^@]+@[^@]+\.[^@]+", text):
            await message.answer("❗ Неверный формат Email. Попробуйте снова:")
            return
        user_state[user_id]["email"] = text
        user_state[user_id]["step"] = "datenschutz"
        text_ds = (
            "📄 Datenschutzerklärung.
"
            "Einverständniserklärung in die Erhebung und Verarbeitung von Daten. "
            "Ich kann diese jederzeit unter email widerrufen.

"
            "Согласие на обработку и хранение персональных данных. "
            "Мне известно, что я могу в любой момент отозвать это согласие по email."
        )
        button = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я согласен", callback_data="agree"))
        await message.answer(text_ds, reply_markup=button)

    elif step == "comment":
        user_state[user_id]["comment"] = text
        data = user_state[user_id]
        row = [
            user_id,
            data.get("name", ""),
            ", ".join(data.get("topics", [])),
            data.get("phone", ""),
            data.get("email", ""),
            data.get("comment", ""),
            "Да",
            ""
        ]
        sheet.append_row(row)
        await message.answer("🎉 Спасибо! Ваша заявка принята. Мы свяжемся с вами.")

@dp.callback_query_handler(lambda c: c.data.startswith("topic:"))
async def topic_handler(callback_query: types.CallbackQuery):
    topic = callback_query.data.split(":", 1)[1]
    user_id = callback_query.from_user.id
    topics = user_state[user_id].setdefault("topics", [])
    if topic not in topics:
        topics.append(topic)
    await callback_query.answer(f"Добавлено: {topic}")

@dp.callback_query_handler(lambda c: c.data == "done_topics")
async def done_topics_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "phone"
    await bot.send_message(user_id, "📞 Введите ваш номер телефона (начинается с +49):")

@dp.callback_query_handler(lambda c: c.data == "agree")
async def agree_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "comment"
    await bot.send_message(user_id, "📝 Оставьте комментарий (если есть):")

app = app
