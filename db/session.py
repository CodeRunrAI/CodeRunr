import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from db.base import Base  # noqa: F401 — re-export for Alembic env.py

logger = logging.getLogger(__name__)


def _build_url(drivername: str) -> str:
    """Build a DB URL string for the given SQLAlchemy driver."""
    url = URL.create(
        drivername=drivername,
        username=settings.POSTGRES_USER.get_secret_value(),
        password=settings.POSTGRES_PASSWORD.get_secret_value(),
        host=settings.POSTGRES_HOST.get_secret_value(),
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB.get_secret_value(),
    )
    logger.info("Database URL: %s", url.render_as_string(hide_password=True))
    return url.render_as_string(hide_password=False)


async_db_url = _build_url("postgresql+asyncpg")
async_engine = create_async_engine(async_db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

sync_db_url = _build_url("postgresql+psycopg2")
sync_engine = create_engine(sync_db_url, echo=False)
SyncSessionLocal = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            raise
        finally:
            await session.close()


def get_sync_db():
    with SyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            raise
        finally:
            session.close()
