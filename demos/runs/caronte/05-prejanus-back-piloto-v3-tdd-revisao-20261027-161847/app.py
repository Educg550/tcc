from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from routers.auth_routes import router as auth_router
from routers.edicts_routes import router as edicts_router
from routers.forms_routes import router as forms_router
from routers.mappings_routes import router as mappings_router
from routers.reports_routes import router as reports_router
from routers.submissions_routes import router as submissions_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=True,
    max_age=8 * 3600,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root():
    return {"message": "Hello World"}


app.include_router(auth_router)
app.include_router(forms_router)
app.include_router(edicts_router)
app.include_router(mappings_router)
app.include_router(reports_router)
app.include_router(submissions_router)
