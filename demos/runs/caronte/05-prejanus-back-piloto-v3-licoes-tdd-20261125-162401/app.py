from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from routers import auth_routes, edicts_routes, forms_routes, submissions_routes

app = FastAPI(title=settings.app_name, version=settings.app_version)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=settings.app_env == "production",
    max_age=8 * 3600,
    session_cookie="session",
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(auth_routes.router)
app.include_router(forms_routes.router)
app.include_router(edicts_routes.router)
app.include_router(submissions_routes.router)
