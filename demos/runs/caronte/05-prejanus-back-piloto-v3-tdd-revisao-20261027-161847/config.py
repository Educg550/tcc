import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.app_name = os.environ.get("APP_NAME", "PreJanus")
        self.app_env = os.environ.get("APP_ENV", "")
        self.app_version = os.environ.get("APP_VERSION", "0.1.0")
        self.db_url = os.environ.get("DB_CONNECTION_STRING", "")
        self.db_forms_url = os.environ.get("DB_CONNECTION_STRING_FORMS", "")
        self.base_url = os.environ.get("BASE_URL", "").rstrip("/")
        self.secret_key = os.environ.get("SECRET_KEY", "prejanus-dev-secret")
        self.dev_user_id = os.environ.get("DEV_USER_ID")
        cors = os.environ.get("BACKEND_CORS_ORIGINS", "")
        self.cors_origins = [o.strip() for o in cors.split(",") if o.strip()]
        self.smtp_host = os.environ.get("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "25"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.from_email = os.environ.get("FROM_EMAIL", "prejanus@example.com")
        self.smtp_use_tls = os.environ.get("SMTP_USE_TLS", "").lower() in ("1", "true", "yes")
        self.su_host = os.environ.get("SENHAUNICA_OAUTH_HOST", "").rstrip("/")
        self.su_request = os.environ.get(
            "SENHAUNICA_REQUEST_TOKEN_RESOURCE", "/wsusuario/oauth/request_token"
        )
        self.su_authorize = os.environ.get(
            "SENHAUNICA_AUTHORIZE_URL", "/wsusuario/oauth/authorize"
        )
        self.su_access = os.environ.get(
            "SENHAUNICA_ACCESS_TOKEN_RESOURCE", "/wsusuario/oauth/access_token"
        )
        self.callback_id = os.environ.get("SENHAUNICA_CALLBACK_ID", "")
        self.consumer_key = os.environ.get("SENHAUNICA_CONSUMER_KEY", "")
        self.consumer_secret = os.environ.get("SENHAUNICA_CONSUMER_SECRET", "")
        self.uploads_dir = os.environ.get("UPLOADS_DIR", "/shared/uploads")
        self.whitelist_file = Path("data/nusp_whitelist.txt")

    @property
    def is_local(self):
        return self.app_env == "local"


settings = Settings()
