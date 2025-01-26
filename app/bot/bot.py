import logging
import asyncio
from aiogram import Bot, Dispatcher, html
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
import httpx
from app.core.scheduler import start_scheduler  # импортируем start_scheduler

# Токен Telegram-бота
API_TOKEN = '8093417419:AAGNe6AbUuFzEin_86wuE0Z_4eJ0MQwSrUY'

# URL вашего API
API_URL = "http://127.0.0.1:8000/api/v1/products"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
kd_list = [[KeyboardButton(text="🔍 Получить данные по товару")]]
# Кнопки для взаимодействия
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

        except Exception as e:
            logging.error(f"Ошибка при запросе к API: {e}")
            reply = f"⚠️ Ошибка при обращении к API: {e}"

    await message.reply(reply)

# Обработчик для остальных текстовых сообщений
@dp.message()
async def echo(message: Message):
    await message.reply("Я могу обработать только артикулы товаров или команды.")

# Запуск бота и планировщика
async def start_bot():
    # Запуск планировщика
    await start_scheduler()

    # Запуск бота
    await dp.start_polling(bot)

# Запуск основного процесса
if __name__ == '__main__':
    asyncio.run(start_bot())
