from fastapi import FastAPI, HTTPException, Body
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field
from typing import Optional
from app.core.tasks import save_product_data  # Ваша асинхронная функция для сохранения данных

# Инициализация FastAPI-приложения
app = FastAPI()

# Инициализация планировщика
scheduler = AsyncIOScheduler()


# Модель для валидации данных
class SchedulerConfig(BaseModel):
    interval_minutes: int = Field(..., ge=1, le=1440, description="Интервал в минутах (1-1440)")
    job_id: Optional[str] = Field(default="periodic_data_collection", description="ID задачи")
    description: Optional[str] = Field(default=None, description="Описание задачи")


async def start_scheduler():
    await save_product_data()
    # Добавление задачи в планировщик
    scheduler.add_job(
        save_product_data,
        IntervalTrigger(minutes=30),
        id="periodic_data_collection",
        replace_existing=True
    )
    # Запуск планировщика
    scheduler.start()


# Запуск планировщика при старте приложения
@app.on_event("startup")
async def startup_event():
    print("Приложение запущено. Планировщик запускается...")
    await start_scheduler()


# Остановка планировщика при завершении приложения
@app.on_event("shutdown")
async def shutdown_event():
    print("Приложение завершает работу. Планировщик останавливается...")
    scheduler.shutdown()


# Эндпоинт для получения текущего состояния
@app.get("/")
async def root():
    return {"message": "Планировщик работает!"}


# Эндпоинт для добавления новой задачи
@app.post("/scheduler/")
async def add_scheduler_task(config: SchedulerConfig = Body(...)):
    try:
        # Проверка на существование задачи с таким ID
        if scheduler.get_job(config.job_id):
            raise HTTPException(status_code=400, detail="Задача с таким ID уже существует.")

        # Добавление новой задачи с пользовательскими настройками
        scheduler.add_job(
            save_product_data,
            IntervalTrigger(minutes=config.interval_minutes),
            id=config.job_id,
            replace_existing=True
        )

        return {
            "message": "Задача успешно добавлена.",
            "task": config.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении задачи: {str(e)}")


# Эндпоинт для удаления задачи
@app.delete("/scheduler/{job_id}")
async def delete_scheduler_task(job_id: str):
    try:
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Задача с указанным ID не найдена.")

        scheduler.remove_job(job_id)
        return {"message": "Задача успешно удалена.", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении задачи: {str(e)}")
