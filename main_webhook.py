from oauth2client.service_account import ServiceAccountCredentials
import os
from fastapi import FastAPI, Request
from starlette.responses import Response
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import json
import gspread


API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_PORT = int(os.getenv("PORT", 8000))
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")


GOOGLE_CREDENTIALS_DICT = {
  "type": "service_account",
  "project_id": "telegram-bot-sheets-462500",
  "private_key_id": "fe96728f4dcc21bb4c393b84370793803eff544d",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCyN+A+qMA1W+67\nvhBPEBjkdUmrf6hBMRQMrhQEs/oCgasgRrJ5Fh4w8URa71hJodjJNyk2cvY1HohQ\n8jkEuvuMOnHhPvPD5msLhfrAE1dNMu6reT9yQxoKyBIUC7YbgwOxMGP40sZfrY07\nbSIO0YcSN42WyE0zHArp+A5/Tb3Zto9FXV1ry2a5LTq5U9gB6YGztlYhyFWcBMWV\nQo09xtiRXwT9S8Ee4DXJd037p0epc40gcPD20RcXA6F24gothcZvmlPQHihaE5b8\ncfysbEOximxVzD2Q1/1WBVAAHIvHdGBiSkN4RT82R42bbc99ju3dRVbJqIaxwgtY\nJiUIcJTrAgMBAAECggEAHVoPMw1Z8q/RxtahGv8SCnZitr3PTpqwVvzzS77/Oxse\nEwfHFyLpwAfMc+mdhysCaElkc+pFMIR3JlXDxvVWE/IAQCe9FWjv/QrePHTdrleS\nxWeyZ7WI0XkYDnh1+rFTkgLf7uLP9ywUlFKqBvoX8+EgZFKtnEWkaoUHO4zolWAx\nyPs6fmNtMXe7KGDjy7Swg3uh2tULyDJWdkRbyAcuqE+F0pgbFCRGIBq6GYiQuO32\nVZ7gZ1kKSuFhE620SA8k/ewZWaP5XTmAvZv+DW49uqYsOte4sSfYTBqUgzDfV0WS\nq8XImeIP/66np6IdiiCTvkMxVgT8d5rHJqSbBXuQUQKBgQDcQA17jFpU/H7SGhHR\nQbzk12cGcX1vtVE9NYMTsqTYwC5ywUt56+fZeuLsNPsSoRFY8jX712fmvOlS+14R\nuWmK1o1mopGZzmgpQyNums7hJB67NXte9UDZMRzZsTjWjkLfLu1/mWlIpD7QnoZH\n6GBSyieitTGqoQys5rb3N0ur4wKBgQDPJUp8teHlXy4rJLlEOHNZaVjagztA6mwQ\nVzS5wPLtYoDWHIWIC4sKLgDGRPH+foVGoodP1E92u15aeWz3I44fohm+S1y/+e2V\n9ERrdGxdYnRgG0PkKR3QmqMlCIiu0vr8trkzGSY3yLwzj6yojWhml2YJLn2dkjd1\nOcpnpXVRWQKBgFEKOGvHPs2agkdoVDn8yDYjk8LpK1BZFOVCtVIgH0upmu2add0M\nkiiRcMGc1O0L2sgxhu99WLursuZXm0tGP7FYNHsZQh2ntufHzle6Gnj4w1361cQg\n1ZWU3pqy/MjlW3GnYLfciMKzvHEigyIePKL5ww+5P+cajwFnetcHv44lAoGAHqsv\nvw0St+oCpOKYB3CwK1G8lQWO9Up/21997+6QSPMnjgvE/WJwIH61IKW+imZjBxUz\nIW+WoEaXbp/BsUlzVl2ioBj6T3YKZgQ3SQ2AqcbU4hHHWHV585Ohie8chX25KUdI\nXjdgACxZKO0hrAbbqSzLL5rRgE3Qpit7OyM1HmkCgYEAsY95ZhfCxiuAfjgpO3iY\nHzCQiCdUdFSyZKBmIqM2yUVL6u/lePjpELKOD8F86Gg9fa5IwDTViARqyLDpsCXL\niOTSth94q1EP1mYp07AkghjeujQRQ/19AgiEEzWqV+pUFvROEnjxh9OHTlYuIVuS\npNWD+igb9RM8ZAzvYlqJGac=\n-----END PRIVATE KEY-----\n",
  "client_email": "telegram-sheets-bot@telegram-bot-sheets-462500.iam.gserviceaccount.com",
  "client_id": "101678910065228926953",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/telegram-sheets-bot%40telegram-bot-sheets-462500.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


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


async def final_thank_you(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_state.get(user_id, {})
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, "✅ Спасибо! Мы свяжемся с вами в течение 24 часов.")

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
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_DICT, scope)
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

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "email")
async def ask_consent(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["email"] = message.text
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
        creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_DICT, scope)
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