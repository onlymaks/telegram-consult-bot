
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types
from aiogram.utils import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import gspread
from oauth2client.service_account import ServiceAccountCredentials

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

Bot.set_current(bot)
Dispatcher.set_current(dp)

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "OK — бот запущен"}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    data = await request.body()
    update = types.Update(**json.loads(data.decode("utf-8")))
    await dp.process_update(update)
    return Response(status_code=200)

user_state = {}

@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
    if args == "consult":
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я согласен", callback_data="consent_given"))
        text = (
        "👋 Добро пожаловать! Этот бот поможет вам записаться на консультацию.\n\n"
        "📌 Мы соблюдаем правила обработки персональных данных (Datenschutz).\n"
        "Вы можете отозвать согласие в любой момент.\n\n"
        "Пожалуйста, подтвердите согласие, чтобы продолжить:"
    )

"
            "📌 Мы соблюдаем правила обработки персональных данных (Datenschutz). "
            "Вы можете отозвать согласие в любой момент.

"
            "Пожалуйста, подтвердите согласие, чтобы продолжить:"
        )
        await message.answer(text, reply_markup=markup)
    else:
        await message.answer("👋 Привет! Напишите, чем я могу помочь.")

@dp.callback_query_handler(lambda c: c.data == "consent_given")
async def ask_name(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id] = {"step": "name"}
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Пожалуйста, введите ваше имя:")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "name")
async def ask_topics(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["name"] = message.text
    user_state[user_id]["step"] = "topics"
    topics = [
        "Государственные субсидии и экономия на налогах",
        "Различные разновидности страхования",
        "Управление личными расходами",
        "Финансирование недвижимости",
        "Стратегия финансового благополучия",
        "Здравоохранение",
        "Пенсионные Планы",
        "Потребительское кредитование",
        "Образование для детей и накопительные программы",
        "Создание дополнительного дохода"
    ]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for topic in topics:
        markup.add(KeyboardButton(topic))
    await message.answer("Выберите интересующие вас темы (по одной):", reply_markup=markup)

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "topics")
async def ask_messenger(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["topics"] = message.text
    user_state[user_id]["step"] = "messenger"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Telegram"), KeyboardButton("WhatsApp"), KeyboardButton("Viber"))
    await message.answer("Выберите удобный мессенджер для связи:", reply_markup=markup)

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "messenger")
async def ask_phone(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["messenger"] = message.text
    user_state[user_id]["step"] = "phone"
    await message.answer("Введите номер телефона (формат +49 XXX XXX XX XX):")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "phone")
async def ask_email(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["phone"] = message.text
    user_state[user_id]["step"] = "email"
    await message.answer("Введите ваш email:")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "email")
async def ask_consent_final(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["email"] = message.text
    user_state[user_id]["step"] = "final_consent"
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я согласен", callback_data="final_yes"))
    text = (
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.
"
        "Ich kann diese jederzeit unter email widerrufen.

"
        "Согласие на обработку и хранение персональных данных.
"
        "Мне известно, что я могу в любой момент отозвать это согласие по email.

"
        "Нажмите «✅ Я согласен», чтобы подтвердить:"
    )
    await message.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "final_yes")
async def final_thank_you(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_state.get(user_id, {})
    await bot.answer_callback_query(callback_query.id)
    summary = (
        f"🆕 Новая заявка:
"
        f"👤 Имя: {data.get('name')}
"
        f"📌 Тема: {data.get('topics')}
"
        f"💬 Мессенджер: {data.get('messenger')}
"
        f"📱 Телефон: {data.get('phone')}
"
        f"📧 Email: {data.get('email')}"
    )
    await bot.send_message(user_id, "✅ Спасибо! Мы свяжемся с вами в течение 24 часов.")
    await bot.send_message(ADMIN_CHAT_ID, summary)

    # Запись в Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    sheet.append_row([
        data.get("name", ""),
        data.get("topics", ""),
        data.get("messenger", ""),
        data.get("phone", ""),
        data.get("email", ""),
        "ДА",
        ""
    ])

    user_state.pop(user_id, None)
