from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from senhaunicapy import SenhaUnica

from src.routers.auth_routers import router as auth_router
from src.routers.edict_routers import router as edict_router
from src.routers.forms_routers import router as forms_router
from src.routers.submission_routers import router as submission_router
from src.settings import get_settings

settings = get_settings()
app = FastAPI()

app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=True, 
    )

app.state.config = {
    "SENHAUNICA_OAUTH_HOST": settings.SENHAUNICA_OAUTH_HOST,
    "SENHAUNICA_REQUEST_TOKEN_RESOURCE": settings.SENHAUNICA_REQUEST_TOKEN_RESOURCE,
    "SENHAUNICA_CONSUMER_KEY": settings.SENHAUNICA_CONSUMER_KEY,
    "SENHAUNICA_CONSUMER_SECRET": settings.SENHAUNICA_CONSUMER_SECRET,
    "SENHAUNICA_AUTHORIZE_URL": settings.SENHAUNICA_AUTHORIZE_URL,
    "SENHAUNICA_ACCESS_TOKEN_RESOURCE": settings.SENHAUNICA_ACCESS_TOKEN_RESOURCE,
    "SENHAUNICA_CALLBACK_ID": settings.SENHAUNICA_CALLBACK_ID
}

senhaunica = SenhaUnica()
senhaunica.init_app(app)

app.include_router(edict_router)
app.include_router(submission_router)
app.include_router(auth_router)
app.include_router(forms_router)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin for origin in settings.BACKEND_CORS_ORIGINS.split(",")
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}