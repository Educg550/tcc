import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


@app.get("/")
def raiz():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/enviar")
def enviar(payload: dict):
    dados = payload.get("dados", payload)  # aceita achatado ou aninhado
    aba = payload.get("aba", "alunos")
    erros = validar(dados, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": montar_oficio(dados, aba)}
