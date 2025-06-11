
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types
from aiogram.utils import json

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
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

# ====== START CONSULTATION ======

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
    if args == "consult":
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я согласен", callback_data="consent_given"))
        text = (
            "👋 Добро пожаловать! Этот бот поможет вам записаться на консультацию.\n\n"
            "📌 Мы соблюдаем правила обработки персональных данных (Datenschutz). "
            "Вы можете отозвать согласие в любой момент.\n\n"
            "Пожалуйста, подтвердите согласие, чтобы продолжить:"
        )
        await message.answer(text, reply_markup=markup)
    else:
        await message.answer("👋 Привет! Напишите, чем я могу помочь.")

@dp.callback_query_handler(lambda c: c.data == "consent_given")
async def step_ask_name(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, введите ваше имя:")
    # Здесь позже начнется FSM или логика шагов

# Тут ты можешь добавить остальные шаги сценария:
# - выбор тем
# - мессенджер
# - телефон
# - email
# - подтверждение

