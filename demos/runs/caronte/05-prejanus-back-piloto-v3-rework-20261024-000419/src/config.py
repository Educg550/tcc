"""Configuração da aplicação, lida de variáveis de ambiente."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PreJanus"
    app_env: str = "local"
    app_version: str = "0.1.0"
    base_url: str = ""
    backend_cors_origins: str = ""
    secret_key: str = "insecure-dev-key"
    db_connection_string: str = ""
    db_connection_string_forms: str = ""
    dev_user_id: int | None = None
    smtp_server: str = "localhost"
    smtp_port: int = 25
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
