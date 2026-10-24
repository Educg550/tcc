"""Ponto de entrada: cria a aplicação e conecta os módulos."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers import auth, edicts, forms, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


app.include_router(auth.router)
app.include_router(edicts.router)
app.include_router(submissions.router)
app.include_router(forms.router)
