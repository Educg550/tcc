import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
app.mount("/assets", StaticFiles(directory=os.path.join(BASE, "assets")), name="assets")


@app.get("/")
def index():
    return FileResponse(os.path.join(BASE, "index.html"))


@app.post("/solicitacao")
def solicitacao(payload: dict):
    from validation import validar
    from letter import oficio

    erros, dados = validar(payload)
    if erros:
        return {"ok": False, "erros": erros, "oficio": ""}
    return {"ok": True, "erros": [], "oficio": oficio(dados)}
