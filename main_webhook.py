from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def read_root():
    return JSONResponse(content={"status": "ok", "message": "Webhook работает!"})

# Пример POST-обработчика для Telegram webhook (можно доработать под свои нужды)
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("Получен апдейт:", data)
    return JSONResponse(content={"status": "received"})