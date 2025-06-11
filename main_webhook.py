import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Бот работает правильно. API_TOKEN получен из .env")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)