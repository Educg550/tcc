from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers import auth, edicts, forms, submissions

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.backend_cors_origins.split(',') if o.strip()],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(edicts.router)
app.include_router(submissions.router)
app.include_router(forms.router)


@app.get('/')
def root():
    return {'message': f'{settings.app_name} v{settings.app_version}'}
