"""Database engines and sessions for the PreJanus and Forms databases."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings


def normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(
    normalize_url(settings.DB_CONNECTION_STRING), pool_pre_ping=True
)
forms_engine = create_engine(
    normalize_url(settings.DB_CONNECTION_STRING_FORMS), pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
FormsSessionLocal = sessionmaker(bind=forms_engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()