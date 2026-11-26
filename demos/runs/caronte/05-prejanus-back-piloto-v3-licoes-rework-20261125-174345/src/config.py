from pathlib import Path

from pydantic_settings import BaseSettings

RAIZ = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    APP_NAME: str = "PreJanus"
    APP_ENV: str = "local"
    APP_VERSION: str = "1.0.0"
    DB_CONNECTION_STRING: str = "postgresql://localhost/caronte_prejanus"
    DB_CONNECTION_STRING_FORMS: str = "postgresql://localhost/caronte_forms"
    BASE_URL: str = "http://localhost:8083"
    BACKEND_CORS_ORIGINS: str = ""
    SECRET_KEY: str = "insecure-dev-key"
    DEV_USER_ID: int | None = None
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "nao-responda@example.com"
    SMTP_USE_TLS: bool = False
    SENHAUNICA_OAUTH_HOST: str = "http://localhost:8181"
    SENHAUNICA_REQUEST_TOKEN_RESOURCE: str = "/wsusuario/oauth/request_token"
    SENHAUNICA_AUTHORIZE_URL: str = "/wsusuario/oauth/authorize"
    SENHAUNICA_ACCESS_TOKEN_RESOURCE: str = "/wsusuario/oauth/access_token"
    SENHAUNICA_CALLBACK_ID: str = ""
    SENHAUNICA_CONSUMER_KEY: str = ""
    SENHAUNICA_CONSUMER_SECRET: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"


settings = Settings()

_WHITELIST: set[str] | None = None


def nusp_whitelist() -> set[str]:
    global _WHITELIST
    if _WHITELIST is None:
        caminho = RAIZ / "data" / "nusp_whitelist.txt"
        valores: set[str] = set()
        if caminho.is_file():
            for linha in caminho.read_text().splitlines():
                for parte in linha.split(","):
                    if parte.strip():
                        valores.add(parte.strip())
        _WHITELIST = valores
    return _WHITELIST
