from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from router_auth import router as auth_router
from router_edicts import router as edicts_router
from router_forms import router as forms_router
from router_submissions import router as submissions_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

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
    max_age=8 * 60 * 60,
    same_site="lax",
    https_only=True,
)

app.include_router(auth_router)
app.include_router(forms_router)
app.include_router(edicts_router)
app.include_router(submissions_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
