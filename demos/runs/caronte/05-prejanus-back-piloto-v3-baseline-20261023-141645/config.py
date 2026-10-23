from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PreJanus"
    app_env: str = "production"
    app_version: str = "0.1.0"
    db_connection_string: str = ""
    db_connection_string_forms: str = ""
    base_url: str = "http://localhost:3000"
    backend_cors_origins: str = ""
    secret_key: str = "changeme"
    dev_user_id: int | None = None
    smtp_server: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@example.com"
    smtp_use_tls: bool = False
    senhaunica_oauth_host: str = ""
    senhaunica_request_token_resource: str = "/wsauth/oauth/request_token"
    senhaunica_authorize_url: str = "/wsauth/oauth/authorize"
    senhaunica_access_token_resource: str = "/wsauth/oauth/access_token"
    senhaunica_callback_id: str = ""
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""


settings = Settings()
