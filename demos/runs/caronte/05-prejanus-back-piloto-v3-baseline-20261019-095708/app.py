from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import cors_origins, settings
from routers import auth, edicts, forms, submissions

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=True,
    max_age=8 * 60 * 60,
)

origins = cors_origins()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(forms.router)
app.include_router(edicts.router)
app.include_router(submissions.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
