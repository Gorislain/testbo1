from fastapi import FastAPI
import asyncio
from aiohttp import web
from app.bot.bot import start_bot  # Импортируем функцию для старта бота
from app.core.database import Base, engine
from app.api.v1.products import router as products_router
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram import Bot, Dispatcher
from app.bot.bot import bot, dp  # Убедитесь, что bot и dp правильно инициализированы

app = FastAPI()

# Инициализация БД
@app.on_event("startup")
async def startup():
    # Создание таблиц при старте приложения
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created!")

    # Настроим webhook для бота
    webhook_url = 'https://stormy-bayou-06853-a62965140369.herokuapp.com/webhook'
    await bot.set_webhook(webhook_url)

    # Запуск бота
    asyncio.create_task(start_bot())  # Если start_bot() запускает приложение aiogram

# Подключение роутеров
app.include_router(products_router, prefix="/api/v1", tags=["products"])

# Запуск приложения через aiohttp и FastAPI
async def start_app():
    # Настроим aiohttp приложение для обработки вебхуков
    app_aiohttp = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app_aiohttp, path='/webhook')

    # Запуск aiohttp сервера с FastAPI приложением
    runner = web.AppRunner(app_aiohttp)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

# Запуск основного приложения
@app.on_event("startup")
async def on_startup():
    await start_app()

# Для запуска FastAPI сервера
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
