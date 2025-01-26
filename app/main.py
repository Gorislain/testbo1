from fastapi import FastAPI
import asyncio
from app.bot.bot import start_bot  # Импортируем функцию для старта бота
from app.core.database import Base, engine
from app.api.v1.products import router as products_router

app = FastAPI()

# Инициализация БД
@app.on_event("startup")
async def startup():
    # Создание таблиц при старте приложения
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created!")
    asyncio.create_task(start_bot())  # Запускаем бота в фоновом потоке

# Подключение роутеров
app.include_router(products_router, prefix="/api/v1", tags=["products"])

# Пример зависимости для работы с сессией
# get_db — это функция, которая возвращает сессию базы данных, которую можно использовать в эндпоинтах