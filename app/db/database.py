from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# The engine connects to the database. 'echo=True' logs all SQL (good for debugging).
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

# A session factory. Calling it creates a new async database session.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # so we can access objects after commit without re-query
)

# Base class for all our models (tables).
class Base(DeclarativeBase):
    pass