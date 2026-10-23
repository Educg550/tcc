"""Configuração da aplicação, lida das variáveis de ambiente."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PreJanus"
    app_env: str = "local"
    app_version: str = "0.1.0"

    db_connection_string: str = ""
    db_connection_string_forms: str = ""

    base_url: str = "http://localhost:8000"
    backend_cors_origins: str = ""
    secret_key: str = "insecure-dev-secret"
    dev_user_id: int | None = None

    smtp_server: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@example.com"
    smtp_use_tls: bool = False

    senhaunica_oauth_host: str = ""
    senhaunica_request_token_resource: str = ""
    senhaunica_authorize_url: str = ""
    senhaunica_access_token_resource: str = ""
    senhaunica_callback_id: str = ""
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""


settings = Settings()

UPLOADS_DIR = "/shared/uploads"
TMP_DIR = "/tmp"
WHITELIST_PATH = "data/nusp_whitelist.txt"


def cors_origins() -> list[str]:
    return [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
