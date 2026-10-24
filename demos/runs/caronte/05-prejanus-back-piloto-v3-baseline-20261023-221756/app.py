from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from routers import auth, edicts, forms, root, submissions


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    origins = [o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Session cookie: 8 hours, SameSite=lax, Secure.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        max_age=8 * 60 * 60,
        same_site="lax",
        https_only=True,
    )

    app.include_router(root.router)
    app.include_router(auth.router)
    app.include_router(forms.router)
    app.include_router(edicts.router)
    app.include_router(submissions.router)
    return app


app = create_app()
