# Telegram Consult Bot

## 🔧 Установка

1. Создай приватный репозиторий на GitHub и загрузи файлы.
2. Создай новый Web Service на [Render](https://render.com/):
   - Environment = Python 3
   - Start command: `uvicorn main_webhook:app --host=0.0.0.0 --port=${PORT:-8000}`
   - Установи переменные окружения:
     - `BOT_TOKEN`
     - `WEBHOOK_URL`
     - `ADMIN_CHAT_ID`
     - `GOOGLE_SHEET_NAME`
3. Загрузи `credentials.json` вручную в Render → "Environment → Secret Files"
4. После запуска, вызови в браузере:
```
https://telegram-consult-bot-s4c7.onrender.com/
```

## ✅ Установка Webhook вручную
Сделай GET-запрос:
```
https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://telegram-consult-bot-s4c7.onrender.com/webhook/<ВАШ_ТОКЕН>
```

## 📄 Google Таблица
Название: `Заявки консультации`  
Столбцы: Имя | Тема | Мессенджер | Телефон | Email | Подтверждение | Комментарий

Убедись, что сервисный аккаунт `telegram-sheets-bot@...` имеет доступ к таблице (через Share).
