from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import date
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

# Modelos
class AlunoForm(BaseModel):
    nome: str
    nusp: str
    programa: str
    nivel: str
    tipo_auxilio: str
    email: str
    evento: str
    periodo: str
    cidade: str
    estado: str
    pais: str
    link: Optional[str] = ""
    valor: str
    detalhamento: str
    apresentacao: str
    logradouro: str
    numero: str
    complemento: Optional[str] = ""
    bairro: str
    cep: str
    cidade_end: str
    estado_end: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


class DocenteForm(BaseModel):
    nome: str
    nusp: str
    programa: str
    email: str
    evento: str
    periodo: str
    cidade: str
    estado: str
    pais: str
    link: Optional[str] = ""
    valor: str
    detalhamento: str
    apresentacao: str
    logradouro: str
    numero: str
    complemento: Optional[str] = ""
    bairro: str
    cep: str
    cidade_end: str
    estado_end: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


# ... endpoints para gerar ofício
