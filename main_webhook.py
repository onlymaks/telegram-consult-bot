import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI, Request
from aiogram.utils.executor import start_webhook
import os

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "YOUR_API_TOKEN")
WEBHOOK_URL_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"https://your-deployment-url.com{WEBHOOK_URL_PATH}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
app = FastAPI()

user_state = {}
user_data = {}

topics = {
    "A": "A. Дотации и налоговая экономика",
    "B": "B. Страховки (авто, мед, адвокат)",
    "C": "C. Накопления на детей",
    "D": "D. Пенсионные планы и дотации",
    "E": "E. Кредиты / Недвижимость",
    "F": "F. Инвестиции и вложения",
    "G": "G. Личные расходы",
    "J": "J. Дополнительный доход",
}

def get_topics_keyboard(selected=None):
    selected = selected or []
    keyboard = InlineKeyboardMarkup(row_width=1)
    for key, label in topics.items():
        mark = "✅ " if key in selected else ""
        keyboard.insert(InlineKeyboardButton(f"{mark}{label}", callback_data=f"topic_{key}"))
    keyboard.insert(InlineKeyboardButton("✅ Готово", callback_data="done_topics"))
    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"step": "consent", "topics": []}
    user_data[user_id] = {}
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я согласен", callback_data="consent_yes"))
    await message.answer(
        "👋 Добро пожаловать! Этот бот поможет вам записаться на консультацию.

"
        "📌 Мы соблюдаем правила обработки персональных данных (Datenschutz). Вы можете отозвать согласие в любой момент.

"
        "Пожалуйста, подтвердите согласие, чтобы продолжить:",
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data == 'consent_yes')
async def consent_confirmed(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "name"
    await bot.send_message(user_id, "Пожалуйста, введите ваше имя:")

@dp.message_handler(lambda message: user_state.get(message.from_user.id, {}).get("step") == "name")
async def process_name(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["name"] = message.text
    user_state[user_id]["step"] = "topics"
    user_state[user_id]["topics"] = []
    await message.answer("Выберите интересующие вас темы (можно несколько):", reply_markup=get_topics_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("topic_"))
async def toggle_topic(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    topic_key = callback_query.data.split("_")[1]
    selected = user_state[user_id].get("topics", [])
    if topic_key in selected:
        selected.remove(topic_key)
    else:
        selected.append(topic_key)
    user_state[user_id]["topics"] = selected
    await bot.edit_message_reply_markup(chat_id=user_id, message_id=callback_query.message.message_id,
                                        reply_markup=get_topics_keyboard(selected))

@dp.callback_query_handler(lambda c: c.data == "done_topics")
async def confirm_topics(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_data[user_id]["topics"] = user_state[user_id]["topics"]
    user_state[user_id]["step"] = "done"
    await bot.send_message(user_id, "✅ Спасибо! Мы свяжемся с вами в течение 24 часов.")

@app.post(WEBHOOK_URL_PATH)
async def webhook_handler(request: Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
