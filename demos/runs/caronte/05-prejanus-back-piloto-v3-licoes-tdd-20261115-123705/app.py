from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from routers import auth as auth_router
from routers import edicts as edicts_router
from routers import forms as forms_router
from routers import submissions as submissions_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=8 * 60 * 60,
        same_site="lax",
        https_only=True,
    )

    origins = settings.cors_origins
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(auth_router.router)
    app.include_router(forms_router.router)
    app.include_router(edicts_router.router)
    app.include_router(submissions_router.router)

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    # Callback OAuth da Senha Única em qualquer caminho: o provedor local
    # notifica o backend com oauth_token e oauth_verifier. Registrado por
    # último para não sombrear as rotas reais.
    @app.api_route("/{full_path:path}", methods=["GET", "POST"])
    async def oauth_callback_catchall(
        full_path: str, request: Request, db=Depends(get_db)
    ):
        params = dict(request.query_params)
        if not (params.get("oauth_token") and params.get("oauth_verifier")):
            raise HTTPException(status_code=404, detail="Não encontrado")
        return await auth_router._login_senhaunica(request, db)

    return app


app = create_app()
