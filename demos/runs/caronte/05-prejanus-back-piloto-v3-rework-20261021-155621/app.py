"""Ponto de entrada: cria e configura a aplicação."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import cors_origins, settings
from routers import auth, edicts, forms, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(edicts.router)
app.include_router(submissions.router)
app.include_router(forms.router)


@app.get("/", tags=["root"])
async def root():
    return {"message": settings.app_name, "version": settings.app_version}
