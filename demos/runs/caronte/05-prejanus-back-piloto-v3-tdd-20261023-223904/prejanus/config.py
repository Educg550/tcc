from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_name: str = "PreJanus"
    app_env: str = "production"
    app_version: str = "0.1.0"
    db_connection_string: str = ""
    db_connection_string_forms: str = ""
    base_url: str = ""
    backend_cors_origins: str = ""
    secret_key: str = "secret"
    dev_user_id: int | None = None
    smtp_server: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "prejanus@example.com"
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
    def whitelist(self) -> set[str]:
        path = Path("data/nusp_whitelist.txt")
        if not path.exists():
            return set()
        out: set[str] = set()
        for chunk in path.read_text(encoding="utf-8").replace(",", "\n").split("\n"):
            chunk = chunk.strip()
            if chunk:
                out.add(chunk)
        return out


settings = Settings()
