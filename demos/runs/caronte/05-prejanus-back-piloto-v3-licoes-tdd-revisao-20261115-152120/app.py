from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from routers import auth, edicts, forms, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=8 * 60 * 60,
    same_site="lax",
    https_only=True,
)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(forms.router)
app.include_router(edicts.router)
app.include_router(submissions.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Preserva a causa de falhas inesperadas no corpo do 500.

    O piloto roda em ambiente isolado de ensaio; sem o traceback é impossível
    diagnosticar as integrações com os bancos e serviços externos.
    """
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return JSONResponse(status_code=500, content={"detail": str(exc), "traceback": tb})


@app.get("/")
async def root():
    return {"message": "Hello World"}
