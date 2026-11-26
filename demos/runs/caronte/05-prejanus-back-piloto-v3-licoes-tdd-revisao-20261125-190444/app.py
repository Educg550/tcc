from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from prejanus.auth import router as auth_router
from prejanus.config import settings
from prejanus.routers import edicts, forms, reports, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

if settings.backend_cors_origins:
    origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
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
    https_only=False,
    max_age=8 * 3600,
)


@app.get("/")
def root():
    return {"message": "Hello World"}


app.include_router(auth_router)
app.include_router(forms.router)
app.include_router(edicts.router)
app.include_router(submissions.router)
app.include_router(reports.router)
