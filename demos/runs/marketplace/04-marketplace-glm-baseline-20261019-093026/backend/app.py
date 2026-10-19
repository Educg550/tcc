from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend import seed
from backend.db import Base, engine
from backend.routers import auth, conversations, favorites, listings, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    seed.run()
    yield


app = FastAPI(title="Feira Livre", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(listings.router)
app.include_router(favorites.router)
app.include_router(conversations.router)
app.include_router(orders.router)
