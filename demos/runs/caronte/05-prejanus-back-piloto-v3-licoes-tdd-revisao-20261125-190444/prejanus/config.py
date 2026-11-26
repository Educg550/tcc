from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "PreJanus"
    app_env: str = "production"
    app_version: str = "0.1.0"
    db_connection_string: str = "postgresql+psycopg://localhost/prejanus"
    db_connection_string_forms: str = "postgresql+psycopg://localhost/forms"
    base_url: str = "http://localhost:8092"
    backend_cors_origins: str = ""
    secret_key: str = "insecure-dev-key"
    dev_user_id: int | None = None
    smtp_server: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "prejanus@example.com"
    smtp_use_tls: bool = False
    senhaunica_oauth_host: str = "http://localhost:8094"
    senhaunica_request_token_resource: str = "/wsusuario/oauth/request_token"
    senhaunica_authorize_url: str = "/wsusuario/oauth/authorize"
    senhaunica_access_token_resource: str = "/wsusuario/oauth/access_token"
    senhaunica_callback_id: str = ""
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""


settings = Settings()
