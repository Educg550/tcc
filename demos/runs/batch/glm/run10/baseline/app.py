from __future__ import annotations
from datetime import date
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydantic import field_validator
import re

app = FastAPI()

@app.get("/")
def read_index():
    return FileResponse(Path("frontend/index.html"))

@app.get("/style.css")
def read_css():
    return FileResponse(Path("frontend/style.css"), media_type="text/css")

@app.get("/app.js")
def read_js():
    return FileResponse(Path("frontend/app.js"), media_type="application/javascript")

# Servir imagens
class AssetReq(BaseModel):
    path: str

@app.post("/api/asset")
def get_asset(r: AssetReq):
    return {"ok": True}

@app.get("/{filename:path}")
def serve_file(filename: str):
    p = Path("assets") / filename
    if p.is_file():
        return FileResponse(p)
    return FileResponse(Path("frontend/index.html"))

# Static mounts
# app.mount("/static", StaticFiles(directory="frontend"), name="static")

# API

import unicodedata

class Info(BaseModel):
    nome: str

@app.post("/api/info")
def info(i: Info):
    return {"echo": i.nome}

@field_validator("nome")
@classmethod
def strip(cls, v):
    return v.strip()

class Form(BaseModel):
    data: str

@app.post("/api/submit")
def submit(f: Form):
    return {"received": f.data, "date": date.today().isoformat()}

async def read_body(req):
    import json
    body = await req.body()
    return json.loads(body) if body else {}

@app.api_route("/api/echo", methods=["GET", "POST"])
async def echo(request):
    return {"method": request.method, "body": await read_body(request)}

class Ping(BaseModel):
    text: str = "ping"

@app.post("/api/ping")
def ping(p: Ping):
    return {"reply": "pong", "you_sent": p.text}

def _is_palindrome(s: str) -> bool:
    s2 = re.sub(r"[^a-z0-9]", "", s.lower())
    return s2 == s2[::-1]

class PalReq(BaseModel):
    text: str

@app.post("/api/palindrome")
def palindrome(p: PalReq):
    return {"text": p.text, "is_palindrome": _is_palindrome(p.text)}

@app.get("/api/date")
def today():
    return {"today": date.today().isoformat()}

