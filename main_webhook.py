
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


@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "topics_select")
async def ask_topics_inline(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["topics"] = []
    user_state[user_id]["step"] = "topics_inline"
    topics = [
        ("Субсидии и налоги", "t1"),
        ("Страхование", "t2"),
        ("Расходы", "t3"),
        ("Недвижимость", "t4"),
        ("Финансовое благополучие", "t5"),
        ("Здравоохранение", "t6"),
        ("Пенсии", "t7"),
        ("Кредиты", "t8"),
        ("Дети", "t9"),
        ("Доход", "t10")
    ]
    markup = InlineKeyboardMarkup(row_width=2)
    for name, code in topics:
        markup.insert(InlineKeyboardButton(name, callback_data=f"topic_{code}"))
    markup.add(InlineKeyboardButton("✅ Готово", callback_data="topics_done"))
    await message.answer("Выберите интересующие вас темы (можно несколько):", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("topic_"))
async def collect_topics(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    code = callback_query.data.replace("topic_", "")
    if "topics" not in user_state[user_id]:
        user_state[user_id]["topics"] = []
    user_state[user_id]["topics"].append(code)
    await bot.answer_callback_query(callback_query.id, text="Добавлено!")

@dp.callback_query_handler(lambda c: c.data == "topics_done")
async def topics_done(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_state[user_id]["step"] = "messenger"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Telegram"), KeyboardButton("WhatsApp"), KeyboardButton("Viber"))
    await bot.send_message(user_id, "Выберите удобный мессенджер для связи:", reply_markup=markup)


@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "name")
async def ask_topics(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["name"] = message.text
    user_state[user_id]["step"] = "topics_select"
    topics = [
        "Государственные субсидии и налоги",
        "Страхование",
        "Личные расходы",
        "Финансирование недвижимости",
        "Финансовое благополучие",
        "Здравоохранение",
        "Пенсионные планы",
        "Потребкредит",
        "Образование детей",
        "Доп. доход"
    ]
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for topic in topics:
        markup.add(KeyboardButton(topic))
    await message.answer("Выберите интересующие вас темы (по одной):", reply_markup=markup)

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "topics")
async def ask_messenger(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["topics"] = message.text
    user_state[user_id]["step"] = "messenger"
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Telegram"), KeyboardButton("WhatsApp"), KeyboardButton("Viber"))
    await message.answer("Выберите удобный мессенджер для связи:", reply_markup=markup)

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

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "email")
async def ask_comment(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["email"] = message.text
    user_state[user_id]["step"] = "comment"
    await message.answer("Добавьте комментарий (необязательно, можно пропустить или отправить -):")

@dp.message_handler(lambda m: user_state.get(m.from_user.id, {}).get("step") == "comment")
async def ask_consent_final(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["comment"] = message.text
    user_state[user_id]["step"] = "final_consent"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Я согласен", callback_data="final_yes")
    )
    text = (
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.\n"
        "Ich kann diese jederzeit unter email widerrufen.\n\n"
        "Согласие на обработку и хранение персональных данных.\n"
        "Мне известно, что я могу в любой момент отозвать это согласие по email.\n\n"
        "Нажмите «✅ Я согласен», чтобы подтвердить:"
    )
    await message.answer(text, reply_markup=markup)

async def ask_consent_final(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["email"] = message.text
    user_state[user_id]["step"] = "comment"
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Я согласен", callback_data="final_yes")
    )
    text = (
        "Datenschutzerklärung. Einverständniserklärung in die Erhebung und Verarbeitung von Daten.\n"
        "Ich kann diese jederzeit unter email widerrufen.\n\n"
        "Согласие на обработку и хранение персональных данных.\n"
        "Мне известно, что я могу в любой момент отозвать это согласие по email.\n\n"
        "Нажмите «✅ Я согласен», чтобы подтвердить:"
    )
    await message.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == "final_yes")
async def final_thank_you(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_state.get(user_id, {})
    await bot.answer_callback_query(callback_query.id)

    # Уведомление пользователю
    await bot.send_message(user_id, "✅ Спасибо! Мы свяжемся с вами в течение 24 часов.")

    # Уведомление администратору
    summary = (
        f"🆕 Новая заявка:\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📌 Тема: {data.get('topics')}\n"
        f"💬 Мессенджер: {data.get('messenger')}\n"
        f"📱 Телефон: {data.get('phone')}\n"
        f"📧 Email: {data.get('email')}"
    )
    await bot.send_message(ADMIN_CHAT_ID, summary)

    # Google Sheets запись
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row([
            data.get("name", ""),
            data.get("topics", ""),
            data.get("messenger", ""),
            data.get("phone", ""),
            data.get("email", ""),
            "ДА",
            data.get("comment", "")
        ])
    except Exception as e:
        print("Ошибка записи в Google Таблицу:", e)

    user_state.pop(user_id, None)
