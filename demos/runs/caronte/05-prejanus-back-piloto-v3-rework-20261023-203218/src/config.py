from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "PreJanus"
    APP_ENV: str = "local"
    APP_VERSION: str = "0.1.0"
    DB_CONNECTION_STRING: str = "postgresql://localhost/prejanus"
    DB_CONNECTION_STRING_FORMS: str = "postgresql://localhost/forms"
    BASE_URL: str = "http://localhost:8000"
    BACKEND_CORS_ORIGINS: str = ""
    SECRET_KEY: str = "dev-secret"
    DEV_USER_ID: int | None = None
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@example.com"
    SMTP_USE_TLS: bool = False
    SENHAUNICA_OAUTH_HOST: str = "http://localhost:8181"
    SENHAUNICA_REQUEST_TOKEN_RESOURCE: str = "/wsusuario/oauth/request_token"
    SENHAUNICA_AUTHORIZE_URL: str = "/wsusuario/oauth/authorize"
    SENHAUNICA_ACCESS_TOKEN_RESOURCE: str = "/wsusuario/oauth/access_token"
    SENHAUNICA_CALLBACK_ID: str = ""
    SENHAUNICA_CONSUMER_KEY: str = ""
    SENHAUNICA_CONSUMER_SECRET: str = ""

    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
