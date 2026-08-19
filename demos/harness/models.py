from pydantic import BaseModel


class Arquivo(BaseModel):
    caminho: str
    conteudo: str


class Mudanca(BaseModel):
    """Única ação que o modelo pode propor: escrever estes arquivos."""

    arquivos: list[Arquivo]


class VeredictoCriterio(BaseModel):
    id: str
    passou: bool
    evidencia: str


class VeredictoCUA(BaseModel):
    criterios: list[VeredictoCriterio]
    aprovado_geral: bool
    resumo: str
