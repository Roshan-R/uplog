from sqlalchemy.ext.asyncio import create_async_engine
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
IP_HASH = os.getenv("IP_HASH")
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
    connect_args = {}
async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # echo=True for SQL logging
)
__all__ = [async_engine, IP_HASH]
