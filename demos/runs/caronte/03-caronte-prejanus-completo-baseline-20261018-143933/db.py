"""Conexões com os dois bancos: PreJanus (persistência) e Forms (consulta/escrita)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings

prejanus_engine = create_engine(settings.PREJANUS_DATABASE_URL, pool_pre_ping=True)
forms_engine = create_engine(settings.FORMS_DATABASE_URL, pool_pre_ping=True)

PrejanusSession = sessionmaker(bind=prejanus_engine, expire_on_commit=False)
FormsSession = sessionmaker(bind=forms_engine, expire_on_commit=False)


def get_db():
    db = PrejanusSession()
    try:
        yield db
    finally:
        db.close()


def get_forms_db():
    fs = FormsSession()
    try:
        yield fs
    finally:
        fs.close()
