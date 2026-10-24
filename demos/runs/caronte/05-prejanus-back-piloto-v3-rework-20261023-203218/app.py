from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers import auth, edicts, forms, mappings, submissions

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(edicts.router)
app.include_router(mappings.router)
app.include_router(submissions.router)
app.include_router(forms.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": settings.APP_NAME}
