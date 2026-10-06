import itertools
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

ROTULOS_ALUNOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

VALORES_PADRAO = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Doutorado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "SBBD",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "20 a 23 de outubro de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "sbbd.org.br",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e inscrição",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Anfiteatro",
    "NÚMERO": "181",
    "COMPLEMENTO": "Sala 224",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "0001",
    "NÚMERO DA CONTA": "12345-6",
}

VARIANTES_DO_VALOR = [
    ("R$ 1.500,00", "R$ 0,00"),
    ("150000", "0"),
    ("1500.00", "0.00"),
    ("1500", "0"),
]

SEM_NA_ABA_DOCENTES = ("NÍVEL", "TIPO DE AUXÍLIO")

_resolvido = {}


def _texto_da_resposta(resposta):
    try:
        dados = resposta.()
    except Exception:
        return resposta.text.replace("\r\n", "\n")

    def achatar(parte):
        if isinstance(parte, str):
            return parte
        if isinstance(parte, dict):
            return "\n".join(achatar(valor) for valor in parte.values())
        if isinstance(parte, (list, tuple)):
            return "\n".join(achatar(item) for item in parte)
        return "" if parte is None else str(parte)

    return achatar(dados).replace("\r\n", "\n")


def _rotas_post():
    rotas = []
    for rota in app.routes:
        caminho = getattr(rota, "path", None)
        metodos = getattr(rota, "methods", set())
        if caminho and "POST" in metodos and "{" not in caminho:
            rotas.append(caminho)
    return rotas


def _chaves(rotulos, esquema):
    if esquema == "rotulo":
        return {rotulo: rotulo for rotulo in rotulos}
    if esquema == "snake":
        return {
            rotulo: re.sub(r"[^a-z0-9]+", "_", rotulo.lower()).strip("_")
            for rotulo in rotulos
        }
    return {rotulo: rotulo.lower() for rotulo in rotulos}


def _postar(cliente, rota, chaves, valores, modo):
    dados = {chaves[rotulo]: valor for rotulo, valor in valores.items()}
    if modo == "":
        return cliente.post(rota, =dados)
    return cliente.post(rota, data=dados)


def _resolver_alunos(cliente):
    if "alunos" in _resolvido:
        return _resolvido["alunos"]
    rotas = _rotas_post()
    if not rotas:
        pytest.fail("o backend não expõe nenhuma rota POST para receber a solicitação")
    for rota, esquema, modo, variante in itertools.product(
        rotas, ("rotulo", "snake", "minusculas"), ("", "form"), VARIANTES_DO_VALOR
    ):
        valores = dict(VALORES_PADRAO)
        valores["VALOR SOLICITADO (R$)"] = variante[0]
        chaves = _chaves(ROTULOS_ALUNOS, esquema)
        texto = _texto_da_resposta(_postar(cliente, rota, chaves, valores, modo))
        if (
            "Interessada(o): Maria da Silva - 1234567" in texto
            and "Valor solicitado: R$ 1.500,00" in texto
            and "Encaminhe-se ao Serviço Financeiro" in texto
        ):
            _resolvido["alunos"] = (rota, chaves, modo, variante)
            return _resolvido["alunos"]
    pytest.fail("nenhuma rota POST aceitou a solicitação válida da aba ALUNOS")


def _resolver_docentes(cliente):
    if "docentes" in _resolvido:
        return _resolvido["docentes"]
    _, chaves_alunos, modo, (valor, _) = _resolver_alunos(cliente)
    rotulos = [rotulo for rotulo in ROTULOS_ALUNOS if rotulo not in SEM_NA_ABA_DOCENTES]
    chaves_resumidas = {rotulo: chaves_alunos[rotulo] for rotulo in rotulos}
    valores_resumidos = {
        rotulo: conteudo
        for rotulo, conteudo in VALORES_PADRAO.items()
        if rotulo in chaves_resumidas
    }
    valores_resumidos["VALOR SOLICITADO (R$)"] = valor
    valores_com_vazios = dict(VALORES_PADRAO)
    valores_com_vazios["VALOR SOLICITADO (R$)"] = valor
    valores_com_vazios["NÍVEL"] = ""
    valores_com_vazios["TIPO DE AUXÍLIO"] = ""
    candidatos = [
        (chaves_resumidas, valores_resumidos),
        (chaves_alunos, valores_com_vazios),
    ]
    for rota in _rotas_post():
        for chaves, valores in candidatos:
            texto = _texto_da_resposta(_postar(cliente, rota, chaves, valores, modo))
            if (
                "Interessada(o): Maria da Silva - 1234567" in texto
                and "Verba do programa" in texto
            ):
                _resolvido["docentes"] = (rota, chaves, valores, modo)
                return _resolvido["docentes"]
    pytest.fail("nenhuma rota POST gerou o ofício da aba DOCENTES")


@pytest.fixture(scope="session")
def cliente():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="session")
def rotulos_alunos():
    return list(ROTULOS_ALUNOS)


@pytest.fixture(scope="session")
def enviar_alunos(cliente):
    rota, chaves, modo, (valor, zero) = _resolver_alunos(cliente)
    _resolvido["valor_zero"] = zero

    def enviar(sobrescrever=None):
        valores = dict(VALORES_PADRAO)
        valores["VALOR SOLICITADO (R$)"] = valor
        if sobrescrever:
            valores.update(sobrescrever)
        return _texto_da_resposta(_postar(cliente, rota, chaves, valores, modo))

    return enviar


@pytest.fixture(scope="session")
def valor_zero(enviar_alunos):
    return _resolvido["valor_zero"]


@pytest.fixture(scope="session")
def enviar_docentes(cliente):
    rota, chaves, valores_base, modo = _resolver_docentes(cliente)

    def enviar(sobrescrever=None):
        valores = dict(valores_base)
        if sobrescrever:
            valores.update(sobrescrever)
        return _texto_da_resposta(_postar(cliente, rota, chaves, valores, modo))

    return enviar


@pytest.fixture(scope="session")
def pagina(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200, "a página inicial não respondeu 200"
    assert "text/html" in resposta.headers.get("content-type", "")
    return resposta.text


@pytest.fixture(scope="session")
def estaticos(cliente, pagina):
    html = pagina.replace("'", '"')
    link = re.search(r'<link[^>]+href="([^"]+\.css[^"]*)"', html)
    script = re.search(r'<script[^>]+src="([^"]+\.js[^"]*)"', html)
    assert link, "a página não referencia um arquivo .css"
    assert script, "a página não referencia um arquivo .js"
    css = cliente.get(link.group(1))
    js = cliente.get(script.group(1))
    assert css.status_code == 200, "o style.css não é servido como estático"
    assert js.status_code == 200, "o app.js não é servido como estático"
    return css.text, js.text
