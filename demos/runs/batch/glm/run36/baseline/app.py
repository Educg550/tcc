from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import date
import re

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ... resto do código backend