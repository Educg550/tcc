from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PreJanus"
    app_env: str = ""
    app_version: str = "0.1.0"
    db_connection_string: str = ""
    db_connection_string_forms: str = ""
    base_url: str = ""
    backend_cors_origins: str = ""
    secret_key: str = "secret"
    dev_user_id: int | None = None
    smtp_server: str = ""
    smtp_port: int = 25
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    smtp_use_tls: bool = False
    senhaunica_oauth_host: str = ""
    senhaunica_request_token_resource: str = "/wsusuario/oauth/request_token"
    senhaunica_authorize_url: str = "/wsusuario/oauth/authorize"
    senhaunica_access_token_resource: str = "/wsusuario/oauth/access_token"
    senhaunica_callback_id: str = ""
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}

UPLOADS_DIR = "/shared/uploads"
TMP_DIR = "/tmp"
WHITELIST_PATH = "data/nusp_whitelist.txt"
SIGNATURE_PATH = "data/signature.png"
LOGO_PATH = "assets/logo.png"
USP_LOGO_PATH = "assets/usp.png"


def load_whitelist() -> set[str]:
    try:
        with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return set()
    values = set()
    for chunk in content.replace("\n", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            values.add(chunk)
    return values


NUSP_WHITELIST = load_whitelist()
