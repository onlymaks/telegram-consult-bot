import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
from starlette.requests import Request
from aiogram.contrib.middlewares.logging import LoggingMiddleware

API_TOKEN = os.getenv("BOT_TOKEN", "your-token-here")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_state = {}

# FastAPI для Render
app = FastAPI()

@app.post("/webhook/{token}")
async def webhook_handler(request: Request):
    body = await request.body()
    update = types.Update.de_json(body.decode("utf-8"))
    await dp.process_update(update)
    return "ok"

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"step": "agree"}
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Согласен", callback_data="agree"))
    await message.answer(
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.
"
        "Ich kann diese jederzeit unter email widerrufen.

"
        "Согласие на обработку и хранение персональных данных.
"
        "Мне известно, что я могу в любой момент отозвать это согласие по email.",
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data == "agree")
async def process_agree(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "name"
    await bot.send_message(user_id, "Как вас зовут?")

@dp.message_handler(lambda message: user_state.get(message.from_user.id, {}).get("step") == "name")
async def process_name(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["name"] = message.text
    user_state[user_id]["step"] = "done"
    await message.answer("Спасибо! Ваша заявка принята.")

@dp.message_handler()
async def fallback(message: types.Message):
    await message.reply("Пожалуйста, начните с /start")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
