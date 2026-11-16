from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from auth import router as auth_router
from config import settings
from routers import edicts, forms, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

origins = [origin.strip() for origin in settings.backend_cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=True,
    max_age=8 * 60 * 60,
)

app.include_router(auth_router)
app.include_router(forms.router)
app.include_router(edicts.router)
app.include_router(submissions.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
