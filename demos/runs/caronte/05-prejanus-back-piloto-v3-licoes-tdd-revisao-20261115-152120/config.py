from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PreJanus"
    app_env: str = "production"
    app_version: str = "0.1.0"

    db_connection_string: str = "postgresql://localhost/prejanus"
    db_connection_string_forms: str = "postgresql://localhost/forms"

    base_url: str = "http://localhost"
    backend_cors_origins: str = ""
    secret_key: str = "insecure-dev-secret"
    dev_user_id: int | None = None

    smtp_server: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@prejanus.local"
    smtp_use_tls: bool = False

    senhaunica_oauth_host: str = ""
    senhaunica_request_token_resource: str = "/wsusuario/oauth/request_token"
    senhaunica_authorize_url: str = "/wsusuario/oauth/authorize"
    senhaunica_access_token_resource: str = "/wsusuario/oauth/access_token"
    senhaunica_callback_id: str = ""
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"


settings = Settings()
