"""Configuração do PreJanus Back por variáveis de ambiente."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "local"
    DEV_USER_ID: str | None = None
    SECRET_KEY: str = "prejanus-dev-secret-key"
    BACKEND_CORS_ORIGINS: list[str] = []

    PREJANUS_DATABASE_URL: str = "postgresql+psycopg://prejanus:prejanus@localhost:5432/prejanus"
    FORMS_DATABASE_URL: str = "postgresql+psycopg://forms:forms@localhost:5432/forms"

    BASE_URL: str = "http://localhost:8083"

    # Senha Única (provedor local que reproduz o contrato OAuth da USP)
    SENHA_UNICA_URL: str = "http://localhost:8001"
    OAUTH_CONSUMER_KEY: str = ""
    OAUTH_CONSUMER_SECRET: str = ""

    # SMTP local do ensaio
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "prejanus@example.com"

    UPLOADS_DIR: str = "/shared/uploads"
    TMP_DIR: str = "/tmp"
    NUSP_WHITELIST_FILE: str = "data/nusp_whitelist.txt"
    SIGNATURE_FILE: str = "data/signature.html"


settings = Settings()
