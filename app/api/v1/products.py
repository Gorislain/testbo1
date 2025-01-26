from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.core.database import get_db
import httpx

router = APIRouter()

WB_URL = "https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm="

@router.post("/products")
async def add_product(data: dict, db: AsyncSession = Depends(get_db)):
    artikul = data.get("artikul")
    if not artikul:
        raise HTTPException(status_code=400, detail="Артикул не указан.")

    # Запрос к Wildberries
    async with httpx.AsyncClient() as client:
        ops = WB_URL + str(artikul)
        response = await client.get(ops)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Ошибка получения данных от Wildberries.{response}, {ops}")
        product_data = response.json()

    # Извлечение данных из ответа
    try:
        product_info = product_data["data"]["products"][0]
        name = product_info["name"]
        price = product_info["salePriceU"] / 100
        rating = product_info.get("rating", 0)
        total_quantity = sum(stock["qty"] for size in product_info["sizes"] for stock in size["stocks"])
    except (KeyError, IndexError):
        raise HTTPException(status_code=400, detail=f"Ошибка обработки данных от Wildberries.{response}, {product_data}")

    result = await db.execute(select(Product).where(Product.artikul == artikul))
    existing_product = result.scalars().first()

    if existing_product is None:
        # Продукт не найден, добавляем его в базу данных
        new_product = Product(
            artikul=artikul,
            name=name,
            price=price,
            rating=rating,
            total_quantity=total_quantity,
        )
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return {"message": "Продукт добавлен в базу данных", "product": new_product}
    else:
        # Продукт уже существует, возвращаем его
        return {"message": "Продукт уже существует в базе данных", "product": existing_product}