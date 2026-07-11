from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from config import settings
from app.db.base import Base

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DB_ECHO,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for background threads (aiomysql not thread-safe)
_sync_engine = None


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.database_url_sync,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            echo=settings.DB_ECHO,
        )
    return _sync_engine


SyncSessionLocal = sessionmaker(class_=Session, expire_on_commit=False)


def get_sync_db() -> Session:
    session = SyncSessionLocal(bind=get_sync_engine())
    try:
        return session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()