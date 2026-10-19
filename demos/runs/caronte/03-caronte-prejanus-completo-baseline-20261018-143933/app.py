"""PreJanus Back — API FastAPI para acompanhamento de processos seletivos."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from db import prejanus_engine
from models import Base

app = FastAPI(title="PreJanus Back", version="2.0")

# Sessão de 8 horas com cookie SameSite=lax (como na interface original).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    max_age=8 * 60 * 60,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(prejanus_engine)


@app.get("/")
def root():
    return {"message": "Hello World"}


from routes_auth import router as auth_router
from routes_forms import router as forms_router
from routes_edicts import router as edicts_router
from routes_submissions import router as submissions_router
from routes_reports import router as reports_router

app.include_router(auth_router)
app.include_router(forms_router)
app.include_router(edicts_router)
app.include_router(submissions_router)
app.include_router(reports_router)
