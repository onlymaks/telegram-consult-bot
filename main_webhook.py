
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import json

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
Bot.set_current(bot)
Dispatcher.set_current(dp)
app = FastAPI()
user_state = {}

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

# === /start с fallback на кнопку ===
@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
    print(f"📩 Параметр /start: {args}")
    if args == "consult":
        await launch_consult(message)
    else:
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📅 Записаться на консультацию", callback_data="open_consult")
        )
        await message.answer("Выберите действие:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "open_consult")
async def handle_consult_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await launch_consult(callback_query.message)

# === Сценарий анкеты ===
async def launch_consult(message):
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
async def ask_name(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id] = {"step": "name"}
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Пожалуйста, введите ваше имя:")
