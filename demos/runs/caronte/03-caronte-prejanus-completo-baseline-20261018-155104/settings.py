from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "production"
    dev_user_id: str | None = None
    backend_cors_origins: str = ""
    base_url: str = "http://localhost:8083"
    prejanus_database_url: str = "postgresql+psycopg://prejanus:prejanus@localhost:5432/prejanus"
    forms_database_url: str = "postgresql+psycopg://forms:forms@localhost:5432/forms"
    uploads_dir: str = "/shared/uploads"
    tmp_dir: str = "/tmp"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = "prejanus@ime.usp.br"
    secret_key: str = "prejanus-secret"
    nusp_whitelist_path: str = "data/nusp_whitelist.txt"
    signature_path: str = "data/signature.html"
    logo_path: str = "data/logo.png"
    senhaunica_consumer_key: str = ""
    senhaunica_consumer_secret: str = ""
    senhaunica_request_token_url: str = ""
    senhaunica_authorize_url: str = ""
    senhaunica_access_token_url: str = ""
    senhaunica_user_data_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
