"""Application configuration, read from environment variables."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "PreJanus"
    APP_ENV: str = "production"
    APP_VERSION: str = "1.0.0"

    DB_CONNECTION_STRING: str = (
        "postgresql+psycopg://prejanus:prejanus@localhost:5432/prejanus"
    )
    DB_CONNECTION_STRING_FORMS: str = (
        "postgresql+psycopg://forms:forms@localhost:5432/forms"
    )

    BASE_URL: str = "http://localhost"
    BACKEND_CORS_ORIGINS: str = ""
    SECRET_KEY: str = "insecure-dev-secret-key"
    DEV_USER_ID: int | None = None

    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "prejanus@usp.br"
    SMTP_USE_TLS: bool = False

    SENHAUNICA_OAUTH_HOST: str = "http://localhost:8090"
    SENHAUNICA_REQUEST_TOKEN_RESOURCE: str = "/wsauth/request_token"
    SENHAUNICA_AUTHORIZE_URL: str = "/wsauth/authorize"
    SENHAUNICA_ACCESS_TOKEN_RESOURCE: str = "/wsauth/access_token"
    SENHAUNICA_CALLBACK_ID: str = ""
    SENHAUNICA_CONSUMER_KEY: str = ""
    SENHAUNICA_CONSUMER_SECRET: str = ""

    UPLOADS_DIR: str = "/shared/uploads"
    TMP_DIR: str = "/tmp"
    WHITELIST_FILE: str = "data/nusp_whitelist.txt"
    SIGNATURE_FILE: str = "data/signature.png"

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()