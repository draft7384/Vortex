"""
Configuración central de la aplicación.
Lee variables de entorno desde .env usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # === Base de datos ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1234@localhost:5432/Vortex"
    DB_ECHO: bool = False

    # === JWT ===
    JWT_SECRET: str = "CAMBIAR_EN_PRODUCCION_ESTA_ES_UNA_LLAVE_TEMPORAL"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # === Aplicación ===
    APP_NAME: str = "Vortex Facturacion & CxC"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # === CORS ===
    CORS_ORIGINS: str = "*"


settings = Settings()
