from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Измененная строка подключения для Docker
DATABASE_URL = "postgresql+asyncpg://ue0qc00r65q5p9:pb9f1df95d9d242d3b1b352665f3fc216dd1ca2c38e42cc570e64eff6e4f639bb@cd1goc44htrmfn.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d70sqoi1b1v2o1"


engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
