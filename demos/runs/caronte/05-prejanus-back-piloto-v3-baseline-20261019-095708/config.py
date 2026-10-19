from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PreJanus"
    app_env: str = "production"
    app_version: str = "1.0.0"

    db_connection_string: str = "postgresql+psycopg://prejanus:prejanus@localhost:5432/prejanus"
    db_connection_string_forms: str = "postgresql+psycopg://forms:forms@localhost:5432/forms"

    base_url: str = "http://localhost:8080"
    backend_cors_origins: str = ""
    secret_key: str = "insecure-dev-secret"
    dev_user_id: int | None = None

    smtp_server: str = "localhost"
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@prejanus.local"
    smtp_use_tls: bool = False

    senhaunica_oauth_host: str = "http://localhost:8090"
    senhaunica_request_token_resource: str = "/wsusuario/oauth/request_token"
    senhaunica_authorize_url: str = "/wsusuario/oauth/authorize"
    senhaunica_access_token_resource: str = "/wsusuario/oauth/access_token"
    senhaunica_callback_id: str = ""
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""

    uploads_dir: str = "/shared/uploads"
    tmp_dir: str = "/tmp"
    whitelist_path: str = "data/nusp_whitelist.txt"

    class Config:
        env_file = ".env"


settings = Settings()


def cors_origins() -> list[str]:
    return [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]


def load_nusp_whitelist() -> set[str]:
    try:
        with open(settings.whitelist_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return set()
    values = set()
    for chunk in content.replace(",", "\n").splitlines():
        chunk = chunk.strip()
        if chunk:
            values.add(chunk)
    return values
