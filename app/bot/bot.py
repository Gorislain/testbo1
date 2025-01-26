import logging
import asyncio
from aiogram import Bot, Dispatcher, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
import httpx
from app.core.scheduler import start_scheduler  # импортируем start_scheduler
from fastapi import FastAPI
from aiogram import types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
import uvicorn
from aiohttp import web

# Токен Telegram-бота
API_TOKEN = '7621472185:AAE48lu9U9gtXrzzzuUzXZlO2EI94G_TCuI'

# URL вашего API
API_URL = "https://stormy-bayou-06853-a62965140369.herokuapp.com/api/v1/products"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# FastAPI приложение
app = FastAPI()

# Кнопки для взаимодействия
kd_list = [[KeyboardButton(text="🔍 Получить данные по товару")]]
keyboard = ReplyKeyboardMarkup(
    keyboard=kd_list,  # Correct list of lists initialization
    resize_keyboard=True
)

# Обработчик команды /start
@dp.message(CommandStart())
async def send_welcome(message: Message):
    await message.reply(
        "Привет! Я помогу вам узнать данные о товарах Wildberries.\n\nНажмите '🔍 Получить данные по товару' или отправьте артикул.",
        reply_markup=keyboard
    )

# Обработчик на кнопку и ввод артикула
@dp.message(lambda message: message.text == "🔍 Получить данные по товару")
async def ask_artikul(message: Message):
    await message.reply("Пожалуйста, отправьте артикул товара:")

# Обработчик на ввод артикула товара (числовое значение)
@dp.message(lambda message: message.text.isdigit())  # Обрабатываем числовые сообщения
async def get_product_data(message: Message):
    artikul = message.text

    # Делаем запрос к вашему API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, json={"artikul": artikul})
            if response.status_code == 200:
                product = response.json().get("product", {})
                # Формируем сообщение с данными
                if product:
                    reply = (
                        f"📦 Название: {product.get('name', 'Неизвестно')}\n"
                        f"🆔 Артикул: {product.get('artikul', 'Неизвестно')}\n"
                        f"💰 Цена: {product.get('price', 'Неизвестно')} руб.\n"
                        f"⭐ Рейтинг: {product.get('rating', 'Неизвестно')}\n"
                        f"📦 Количество на всех складах: {product.get('total_quantity', 'Неизвестно')}"
                    )
                else:
                    reply = "⚠️ Не удалось найти товар с этим артикулом."
            else:
                reply = f"⚠️ Ошибка: {response.json().get('detail', 'Не удалось получить данные.')}"
        except httpx.HTTPStatusError as e:
            logging.error(f"Ошибка HTTP: {e}")
            reply = "⚠️ Произошла ошибка при запросе данных от API."
        except httpx.RequestError as e:
            logging.error(f"Ошибка запроса: {e}")
            reply = "⚠️ Произошла ошибка при отправке запроса к API."
        except Exception as e:
            logging.error(f"Неизвестная ошибка: {e}")
            reply = f"⚠️ Ошибка при обращении к API: {e}"

    await message.reply(reply)

# Обработчик для остальных текстовых сообщений
@dp.message()
async def echo(message: Message):
    await message.reply("Я могу обработать только артикулы товаров или команды.")

# Устанавливаем webhook
@app.on_event("startup")
async def on_start():
    webhook_url = 'https://stormy-bayou-06853-a62965140369.herokuapp.com/webhook'
    await bot.set_webhook(webhook_url)

# Webhook endpoint
@app.post("/webhook")
async def webhook(update: dict):
    try:
        update_obj = types.Update(**update)
        await dp.process_update(update_obj)
    except Exception as e:
        logging.error(f"Ошибка при обработке вебхука: {e}")

# Запуск бота и вебхуков
async def start_bot():
    # Запуск планировщика
    await start_scheduler()

    # Настроим aiohttp приложение
    app_aiohttp = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app_aiohttp, path='/webhook')

    # Запуск aiohttp сервера с FastAPI приложением
    runner = web.AppRunner(app_aiohttp)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

# Запуск основного процесса
if __name__ == '__main__':
    asyncio.run(start_bot())
