
import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from fastapi import FastAPI, Request
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "") + WEBHOOK_PATH
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    name = State()
    topics = State()
    email = State()
    confirm = State()

app = FastAPI()

@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return {"ok": True}

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await Form.name.set()
    await message.answer("👋 Введите, пожалуйста, ваше имя (минимум 3 символа):")

@dp.message_handler(state=Form.name)
async def handle_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❌ Некорректное имя. Введите ещё раз (минимум 3 символа):")
        return
    await state.update_data(name=name)
    await Form.topics.set()
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(text=topic, callback_data=topic) for topic in ["Консультация", "Страхование", "Инвестиции", "Кредитование"]]
    keyboard.add(*buttons)
    await message.answer("📌 Выберите интересующие темы (нажмите одну или несколько):", reply_markup=keyboard)

@dp.callback_query_handler(state=Form.topics)
async def handle_topics(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    selected = user_data.get("topics", [])
    topic = callback_query.data
    if topic not in selected:
        selected.append(topic)
    await state.update_data(topics=selected)
    await callback_query.answer(f"✅ {topic} добавлено. Нажмите 'Далее', если выбрали всё.", show_alert=False)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="➡️ Далее", callback_data="done"))
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "done", state=Form.topics)
async def handle_topics_done(callback_query: types.CallbackQuery, state: FSMContext):
    await Form.email.set()
    await callback_query.message.answer("📧 Введите ваш email:")

@dp.message_handler(state=Form.email)
async def handle_email(message: types.Message, state: FSMContext):
    email = message.text.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await message.answer("❌ Некорректный email. Введите ещё раз:")
        return
    await state.update_data(email=email)
    await Form.confirm.set()
    text = (
        "📄 Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.\n"
        "Ich kann diese jederzeit unter email widerrufen.\n\n"
        "Согласие на обработку и хранение персональных данных.\n"
        "Мне известно, что я могу в любой момент отозвать это согласие по email."
    )
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Я согласен", callback_data="confirm")
    )
    await message.answer(text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "confirm", state=Form.confirm)
async def handle_confirm(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
# Строка заменена и завершена корректно
text = f"🎉 Спасибо, {data['name']}!"\nТемы: {', '.join(data['topics'])}
Email: {data['email']}"
    await bot.send_message(callback_query.from_user.id, text)
    await state.finish()

if __name__ == "__main__":
    import asyncio
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
