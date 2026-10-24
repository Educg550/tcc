from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.routers import auth, edicts, forms, submissions

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(edicts.router)
app.include_router(forms.router)
app.include_router(submissions.router)


@app.get('/')
async def root():
    return {'app': settings.app_name, 'version': settings.app_version,
            'environment': settings.app_env}
