from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra='ignore')

    app_name: str = 'PreJanus'
    app_env: str = 'local'
    app_version: str = '0.1.0'

    db_connection_string: str = 'postgresql://localhost/prejanus'
    db_connection_string_forms: str = 'postgresql://localhost/forms'

    base_url: str = 'http://localhost:8080'
    backend_cors_origins: str = ''
    secret_key: str = 'insecure-dev-key'
    dev_user_id: int | None = None

    smtp_server: str = 'localhost'
    smtp_port: int = 1025
    smtp_user: str = ''
    smtp_password: str = ''
    from_email: str = 'noreply@example.com'
    smtp_use_tls: bool = False

    senhaunica_oauth_host: str = 'http://localhost:8181'
    senhaunica_request_token_resource: str = 'wsusuario/oauth/request_token'
    senhaunica_authorize_url: str = 'wsusuario/oauth/authorize'
    senhaunica_access_token_resource: str = 'wsusuario/oauth/access_token'
    senhaunica_callback_id: str = 'prejanus'
    senhaunica_consumer_key: str = ''
    senhaunica_consumer_secret: str = ''

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(',') if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
