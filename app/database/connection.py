import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


raw_url = settings.DATABASE_URL

if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://")

if raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
    raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://")

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Required for Supabase local connections

engine = create_async_engine(
    raw_url,
    echo=False,
    connect_args={"ssl": ssl_context}
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for the duration of a request."""
    async with async_session() as session:
        yield session
