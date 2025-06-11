
import os
import re
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
    user_state[user_id] = {"step": "name"}
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Пожалуйста, введите ваше имя (не менее 3 символов):")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "name")
async def handle_name(message: types.Message):
    user_id = message.from_user.id
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❌ Имя должно содержать минимум 3 символа. Повторите ввод:")
        return
    user_state[user_id]["name"] = name
    user_state[user_id]["step"] = "topics"
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
    msg = await bot.send_message(user_id, "Выберите интересующие вас темы (можно несколько):", reply_markup=markup)
    user_state[user_id]["topics_message_id"] = msg.message_id
    user_state[user_id]["topics"] = []

@dp.callback_query_handler(lambda c: c.data.startswith("topic_"))
async def toggle_topic(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    code = callback_query.data.replace("topic_", "")
    selected = user_state[user_id].get("topics", [])
    if code in selected:
        selected.remove(code)
    else:
        selected.append(code)
    user_state[user_id]["topics"] = selected
    message_id = user_state[user_id].get("topics_message_id")
    await bot.answer_callback_query(callback_query.id)
    if message_id:
        await send_topic_selection(user_id, message_id=message_id)

@dp.callback_query_handler(lambda c: c.data == "topics_done")
async def handle_topics_done(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "messenger"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Telegram"), KeyboardButton("WhatsApp"), KeyboardButton("Viber"))
    await bot.send_message(user_id, "Выберите удобный мессенджер:", reply_markup=markup)
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "messenger")
async def handle_messenger(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["messenger"] = message.text
    user_state[user_id]["step"] = "phone"
    await message.answer("Введите номер телефона (формат +49 XXX XXX XX XX):")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "phone")
async def handle_phone(message: types.Message):
    user_id = message.from_user.id
    phone = message.text.strip()
    if not phone.startswith("+49") or len(phone) < 10:
        await message.answer("❌ Номер должен начинаться с +49 и быть не короче 10 символов. Повторите ввод:")
        return
    user_state[user_id]["phone"] = phone
    user_state[user_id]["step"] = "email"
    await message.answer("Введите ваш email:")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "email")
async def handle_email(message: types.Message):
    import re
    user_id = message.from_user.id
    email = message.text.strip()
    if not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        await message.answer("❌ Некорректный формат email. Повторите ввод:")
        return
    user_state[user_id]["email"] = email
    user_state[user_id]["step"] = "consent"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Я согласен", callback_data="consent_yes")
    )
    text = (
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.\n"
        "Ich kann diese jederzeit unter email widerrufen.\n\n"
        "Согласие на обработку и хранение персональных данных.\n"
        "Мне известно, что я могу в любой момент отозвать это согласие по email.\n\n"
        "Нажмите «✅ Я согласен», чтобы подтвердить:"
    )
    await message.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "consent_yes")
async def ask_comment(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "comment"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "Добавьте комментарий (необязательно, можно отправить -):")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "comment")
async def handle_comment(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["comment"] = message.text
    data = user_state.get(user_id, {})
    await message.answer("✅ Спасибо! Мы свяжемся с вами в течение 24 часов.")
    topics = ", ".join(data.get("topics", []))
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
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row([
            data.get("name", ""), topics, data.get("messenger", ""), data.get("phone", ""),
            data.get("email", ""), "ДА", data.get("comment", "")
        ])
    except Exception as e:
        print("Ошибка записи в Google Таблицу:", e)
    user_state.pop(user_id, None)
