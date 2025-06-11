import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    args = message.get_args()
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
    user_state[user_id] = {"step": "topics_select"}
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Пожалуйста, введите ваше имя:")

# Этот блок добавлен после ввода имени
@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "topics_select")
async def start_topics(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["name"] = message.text
    user_state[user_id]["topics"] = []
    user_state[user_id]["step"] = "topics_inline"
    await send_topic_selection(user_id)

async def send_topic_selection(user_id, message_id=None):
    all_topics = [
        ("A. Дотации и налоговая экономия", "A"),
        ("B. Страховки (авто, мед, адвокат)", "B"),
        ("C. Накопления на детей", "C"),
        ("D. Пенсионные планы и дотации", "D"),
        ("E. Кредиты / Недвижимость", "E"),
        ("F. Инвестиции и вложения", "F"),
        ("G. Личные расходы", "G"),
        ("J. Дополнительный доход", "J")
    ]
    markup = InlineKeyboardMarkup(row_width=1)
    selected = user_state.get(user_id, {}).get("topics", [])
    for label, code in all_topics:
        display = f"✅ {label}" if code in selected else label
        markup.add(InlineKeyboardButton(display, callback_data=f"topic_{code}"))
    markup.add(InlineKeyboardButton("✅ Готово", callback_data="topics_done"))

    if message_id:
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=markup)
    else:
        msg = await bot.send_message(user_id, "Выберите интересующие вас темы (можно несколько):", reply_markup=markup)
        if user_state.get(user_id):
            user_state[user_id]["topics_message_id"] = msg.message_id

@dp.callback_query_handler(lambda c: c.data.startswith("topic_"))
async def toggle_topic(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_state:
        user_state[user_id] = {"topics": [], "step": "topics_inline"}
    code = callback_query.data.replace("topic_", "")
    selected = user_state[user_id].get("topics", [])
    if code in selected:
        selected.remove(code)
    else:
        selected.append(code)
    user_state[user_id]["topics"] = selected
    await bot.answer_callback_query(callback_query.id)
    message_id = user_state[user_id].get("topics_message_id")
    if message_id:
        await send_topic_selection(user_id, message_id=message_id)

@dp.callback_query_handler(lambda c: c.data == "topics_done")
async def topics_done(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "messenger"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Telegram"), KeyboardButton("WhatsApp"), KeyboardButton("Viber"))
    await bot.send_message(user_id, "Выберите удобный мессенджер для связи:", reply_markup=markup)

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


async def ask_comment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "comment"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Добавьте комментарий (необязательно, можно отправить -):")


@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "email")
async def ask_consent_after_email(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["email"] = message.text
    user_state[user_id]["step"] = "consent"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Обязательно для ответа: ДА", callback_data="consent_yes")
    )
    text = (
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.
"
        "Ich kann diese jederzeit unter email widerrufen.

"
        "Согласие на обработку и хранение персональных данных.
"
        "Мне известно, что я могу в любой момент отозвать это согласие по email."
    )
    await message.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "consent_yes")
async def ask_comment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "comment"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Добавьте комментарий (необязательно, можно отправить -):")


@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "comment")
async def final_thank_you(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["comment"] = message.text
    data = user_state.get(user_id, {})
    await message.answer("✅ Спасибо! Мы свяжемся с вами в течение 24 часов.")

    # Уведомление администратору
    topics = ', '.join(data.get("topics", []))
    summary = (
        f"🆕 Новая заявка:\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📌 Темы: {topics}\n"
        f"💬 Мессенджер: {data.get('messenger')}\n"
        f"📱 Телефон: {data.get('phone')}\n"
        f"📧 Email: {data.get('email')}\n"
        f"💬 Комментарий: {data.get('comment')}"
    )
    await bot.send_message(ADMIN_CHAT_ID, summary)

    # Запись в Google Таблицу
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row([
            data.get("name", ""),
            topics,
            data.get("messenger", ""),
            data.get("phone", ""),
            data.get("email", ""),
            "ДА",
            data.get("comment", "")
        ])
    except Exception as e:
        print("Ошибка записи в Google Таблицу:", e)

    user_state.pop(user_id, None)