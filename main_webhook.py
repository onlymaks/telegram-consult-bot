
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()

@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    body = await request.body()
    update = types.Update.de_json(body.decode("utf-8"))
    await dp.process_update(update)
    return Response(status_code=200)
