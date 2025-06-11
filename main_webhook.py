
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Конфигурация ===
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

# === Диагностика параметра start ===
@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
    print(f"📩 Параметр /start: {args}")  # Вывод в консоль Render
    await message.answer(f"👋 Бот получил команду /start с параметром: {args}")
