"""
Capa de conexión a la base de datos PostgreSQL.
Encapsula la creación del engine async, la sesión y la dependency para FastAPI.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import settings


# Engine async con pool de conexiones
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    poolclass=AsyncAdaptedQueuePool,
)

# Fábrica de sesiones async
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency de FastAPI que provee una sesión de DB por request.
    Se cierra automáticamente al finalizar (gracias a `yield`).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
