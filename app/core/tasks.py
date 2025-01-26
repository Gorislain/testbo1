import asyncio
from sqlalchemy.future import select
from app.core.database import async_session
from app.models.product import Product
import httpx  # Используем httpx для асинхронных запросов

async def get_product_data(artikul):
    """
    Асинхронная функция для запроса данных о продукте с Wildberries.
    """
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()  # Возвращаем данные о продукте
    except httpx.RequestError as e:
        print(f"Ошибка при запросе артикула {artikul}: {e}")
        return None

async def save_product_data():
    """
    Сбор данных о продуктах и их сохранение в базе данных.
    Список артикулов извлекается из базы данных.
    """
    # Работа с базой данных через сессию
    async with async_session() as session:
        # Извлекаем список артикулов из базы данных
        result = await session.execute(select(Product.artikul))
        artikuls = [row[0] for row in result.fetchall()]  # Получаем список артикулов

        if not artikuls:
            print("Нет артикулов для обновления.")
            return

        # Создаём список задач для получения данных по продуктам
        tasks = [get_product_data(artikul) for artikul in artikuls]

        # Ждём завершения всех задач
        product_data_list = await asyncio.gather(*tasks)

        # Перебираем полученные данные и обновляем или добавляем продукты в базу
        async with async_session() as session:
            for artikul, product_data in zip(artikuls, product_data_list):
                if product_data is None:
                    continue  # Пропускаем ошибочные данные

                # Извлечение данных из ответа API
                try:
                    product_info = product_data["data"]["products"][0]
                    name = product_info["name"]
                    price = product_info["salePriceU"] / 100
                    rating = product_info.get("rating", 0)
                    total_quantity = sum(stock["qty"] for size in product_info["sizes"] for stock in size["stocks"])

                    # Проверяем наличие продукта в базе данных
                    result = await session.execute(select(Product).where(Product.artikul == artikul))
                    existing_product = result.scalars().first()

                    if existing_product:
                        # Продукт найден, обновляем его данные
                        existing_product.name = name
                        existing_product.price = price
                        existing_product.rating = rating
                        existing_product.total_quantity = total_quantity
                        print(f"Продукт обновлён: {name} (артикул {artikul})")
                    else:
                        # Продукт не найден, добавляем его
                        new_product = Product(
                            artikul=artikul,
                            name=name,
                            price=price,
                            rating=rating,
                            total_quantity=total_quantity
                        )
                        session.add(new_product)
                        print(f"Продукт добавлен: {name} (артикул {artikul})")

                except KeyError:
                    print(f"Ошибка обработки данных для артикула {artikul}: недостаточно данных.")
                    continue

            # Сохраняем изменения в базе данных
            await session.commit()
