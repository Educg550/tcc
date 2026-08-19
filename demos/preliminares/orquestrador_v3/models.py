from pydantic import BaseModel


class Passo(BaseModel):
    acao: str
    resultado_esperado: str


class Criterio(BaseModel):
    id: str
    descricao: str
    passos: list[Passo]


class Criterios(BaseModel):
    criterios: list[Criterio]


class VeredictoCriterio(BaseModel):
    id: str
    passou: bool
    evidencia: str


class VeredictoCUA(BaseModel):
    criterios: list[VeredictoCriterio]
    aprovado_geral: bool
    resumo: str
