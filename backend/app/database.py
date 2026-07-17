from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection

from app.config import get_settings

settings = get_settings()

is_sqlite = "sqlite" in settings.database_url

# SQLite needs check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Convert async URL to sync URL
sync_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")

engine = create_engine(
    sync_url,
    pool_size=settings.database_pool_size if not is_sqlite else 5,
    max_overflow=settings.database_max_overflow if not is_sqlite else 10,
    echo=settings.app_debug,
    connect_args=connect_args,
)

# SQLite 启用 WAL 模式提升并发
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()


SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入 - 获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

