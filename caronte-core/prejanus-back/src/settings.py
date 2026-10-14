from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    APP_VERSION: str

    BASE_URL: str

    # DB
    DB_CONNECTION_STRING: str
    DB_CONNECTION_STRING_FORMS: str

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://127.0.0.1"

    # SMTP
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    SMTP_USE_TLS: bool = False

    SECRET_KEY: str

    SENHAUNICA_CONSUMER_KEY: str
    SENHAUNICA_CONSUMER_SECRET: str

    SENHAUNICA_OAUTH_HOST: str
    SENHAUNICA_ACCESS_TOKEN_RESOURCE: str
    SENHAUNICA_AUTHORIZE_URL: str
    SENHAUNICA_REQUEST_TOKEN_RESOURCE: str
    SENHAUNICA_CALLBACK_ID: str

    # Local dev auth bypass — only honoured when APP_ENV=local
    DEV_USER_ID: Optional[int] = None

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = None 

def get_settings():
    global settings
    if settings is None:
        settings = Settings() 
    return settings
