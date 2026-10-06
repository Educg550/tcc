from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from cartorio import Oficio, oficio_docente, oficio_aluno, valida


class App(FastAPI):
    def __init__(self):
        super().__init__()

        raiz = Path(__file__).resolve().parent
        self.mount("/assets", StaticFiles(directory=raiz / "assets"), name="assets")
        self.mount("/", StaticFiles(directory=raiz, html=True), name="estaticos")

    async def oficio(self, dados: Oficio) -> HTMLResponse:
        erros = valida(dados)
        if erros:
            return HTMLResponse("\n".join(erros), status_code=422)
        corpo = oficio_docente(dados) if dados.aba == "DOCENTES" else oficio_aluno(dados)
        return HTMLResponse(corpo, status_code=200)


app = App()
