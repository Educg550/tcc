import 
import re
import unicodedata

import pytest
from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

DADOS = {
    "nome": "Maria Silva Campos",
    "n_usp": "1034567",
    "programa": "Matemática Aplicada",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria.silva@usp.br",
    "nome_evento": "Workshop de Topologia",
    "periodo": "10 e 11 de março de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link": "https://www.ime.usp.br/eventos/topologia",
    "valor": "R$ 1.500,00",
    "detalhamento": "Passagem aérea e uma diária de hospedagem.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "181",
    "complemento": "Sala 214",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}

REGRAS = [
    ("nome", lambda n: "completo" in n),
    ("cpf", lambda n: "cpf" in n),
    ("cep", lambda n: "cep" in n),
    ("email", lambda n: "email" in n),
    ("n_usp", lambda n: "usp" in n),
    ("programa", lambda n: "programa" in n),
    ("nivel", lambda n: "nivel" in n),
    ("tipo_auxilio", lambda n: "auxilio" in n),
    ("banco", lambda n: "banco" in n),
    ("agencia", lambda n: "agencia" in n),
    ("conta", lambda n: "conta" in n),
    ("data_nascimento", lambda n: "nascimento" in n),
    ("detalhamento", lambda n: "detalh" in n),
    ("apresentacao", lambda n: "apresent" in n or "trabalho" in n),
    ("periodo", lambda n: "periodo" in n),
    ("cidade_evento", lambda n: "cidade" in n and "evento" in n),
    ("estado_evento", lambda n: "estado" in n and "evento" in n),
    ("pais_evento", lambda n: "pais" in n),
    ("link", lambda n: "link" in n),
    ("complemento", lambda n: "complemento" in n),
    ("bairro", lambda n: "bairro" in n),
    ("logradouro", lambda n: "logradouro" in n or "endereco" in n or n == "rua"),
    ("numero", lambda n: "numero" in n or n == "num"),
    ("rg_rnm", lambda n: "rg" in n or "rnm" in n),
    ("nome_evento", lambda n: "evento" in n or "banca" in n),
    ("cidade", lambda n: "cidade" in n),
    ("estado", lambda n: "estado" in n),
    ("valor", lambda n: "valor" in n),
    ("nome", lambda n: n == "nome"),
]

CHAVES_PADRAO = {
    "nome": "nome_completo",
    "n_usp": "n_usp",
    "programa": "programa",
    "nivel": "nivel",
    "tipo_auxilio": "tipo_auxilio",
    "email": "email",
    "nome_evento": "nome_evento",
    "periodo": "periodo_evento",
    "cidade_evento": "cidade_evento",
    "estado_evento": "estado_evento",
    "pais_evento": "pais_evento",
    "link": "link_evento",
    "valor": "valor_solicitado",
    "detalhamento": "detalhamento",
    "apresentacao": "apresentacao_trabalho",
    "data_nascimento": "data_nascimento",
    "logradouro": "logradouro",
    "numero": "numero",
    "complemento": "complemento",
    "bairro": "bairro",
    "cep": "cep",
    "cidade": "cidade",
    "estado": "estado",
    "cpf": "cpf",
    "rg_rnm": "rg_rnm",
    "banco": "nome_banco",
    "agencia": "agencia",
    "conta": "numero_conta",
}

MUDANCAS = [
    {},
    {"valor": "1500"},
    {"valor": "150000"},
    {"cpf": "12345678909", "cep": "05508090", "data_nascimento": "01021980"},
    {"valor": "1500", "cpf": "12345678909", "cep": "05508090", "data_nascimento": "01021980"},
    {"valor": "150000", "cpf": "12345678909", "cep": "05508090", "data_nascimento": "01021980"},
]


def _norm(texto):
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def _texto(resposta):
    try:
        return .dumps(resposta.(), ensure_ascii=False)
    except Exception:
        return resposta.text


def _mapear(props):
    if not props:
        onde = dict(CHAVES_PADRAO)
        corpo = {prop: DADOS[chave] for chave, prop in onde.items()}
        return corpo, None, onde
    corpo, onde, bandeira = {}, {}, None
    resto = dict(props)
    for chave, casa in REGRAS:
        for prop in list(resto):
            if casa(_norm(prop)):
                corpo[prop] = DADOS[chave]
                onde[chave] = prop
                del resto[prop]
                break
    for prop in resto:
        n = _norm(prop)
        if ("aba" in n or "formulario" in n or "perfil" in n
                or "origem" in n or ("tipo" in n and "solicit" in n)):
            bandeira = prop
    return corpo, bandeira, onde


def _tipar(corpo, props, onde):
    for prop, valor in list(corpo.items()):
        if props.get(prop, {}).get("type") not in ("integer", "number"):
            continue
        if not isinstance(valor, str):
            continue
        if onde.get("valor") == prop:
            corpo[prop] = 1500
        else:
            digitos = re.sub(r"[^0-9]", "", valor)
            corpo[prop] = int(digitos) if digitos else valor
    return corpo


def _candidatos(corpo, onde, bandeira):
    bandeiras = [None, "alunos", "aluno", "ALUNOS"] if bandeira else [None]
    for valor_bandeira in bandeiras:
        for mudanca in MUDANCAS:
            corpo_novo = dict(corpo)
            for chave, valor in mudanca.items():
                if chave in onde:
                    corpo_novo[onde[chave]] = valor
            if valor_bandeira is not None:
                corpo_novo[bandeira] = valor_bandeira
            yield corpo_novo


def _rotas_post():
    spec = cliente.get("/openapi.").()
    rotas = []
    for rota, operacoes in spec.get("paths", {}).items():
        if "post" not in operacoes:
            continue
        operacao = operacoes["post"]
        esquema = (operacao.get("requestBody", {}).get("content", {})
                   .get("application/", {}).get("schema", {}))
        if "$ref" in esquema:
            componentes = spec.get("components", {}).get("schemas", {})
            esquema = componentes.get(esquema["$ref"].split("/")[-1], {})
        props = dict(esquema.get("properties", {}))
        for parametro in operacao.get("parameters", []):
            props[parametro["name"]] = parametro.get("schema", {})
        rotas.append((rota, props))
    assert rotas, "backend não expõe nenhuma rota POST"
    rotas.sort(key=lambda item: -len(_mapear(item[1])[0]))
    return rotas


def _probe(corpos, rota):
    for corpo in corpos:
        texto = _texto(cliente.post(rota, =corpo))
        if "Interessada(o): Maria Silva Campos" in texto and "R$ 1.500,00" in texto:
            return {"rota": rota, "corpo": corpo, "texto": texto}
    return None


@pytest.fixture(scope="module")
def alunos():
    for rota, props in _rotas_post():
        corpo, bandeira, onde = _mapear(props)
        corpo = _tipar(corpo, props, onde)
        achado = _probe(_candidatos(corpo, onde, bandeira), rota)
        if achado is not None:
            achado["onde"] = onde
            return achado
    pytest.fail("submissão válida de aluno não devolveu o ofício com os dados preenchidos")


@pytest.fixture(scope="module")
def docentes(alunos):
    corpo = {prop: valor for prop, valor in alunos["corpo"].items()
             if valor not in (DADOS["nivel"], DADOS["tipo_auxilio"])}
    for rota, props in _rotas_post():
        _, bandeira, _ = _mapear(props)
        if bandeira is None:
            tentativas = [dict(corpo)]
        else:
            sem_bandeira = {p: v for p, v in corpo.items() if p != bandeira}
            tentativas = [
                sem_bandeira,
                {**corpo, bandeira: "docentes"},
                {**corpo, bandeira: "docente"},
                {**corpo, bandeira: "DOCENTES"},
            ]
        for corpo_docente in tentativas:
            texto = _texto(cliente.post(rota, =corpo_docente))
            if "Verba do programa" in texto:
                return {"texto": texto}
    pytest.fail("submissão válida de docente não devolveu o ofício da verba do programa")


def _responder(alunos, **substituicoes):
    corpo = dict(alunos["corpo"])
    for chave, valor in substituicoes.items():
        prop = alunos["onde"].get(chave)
        assert prop is not None, f"campo {chave} ausente do corpo da requisição"
        corpo[prop] = valor
    return _texto(cliente.post(alunos["rota"], =corpo))


def test_oficio_do_aluno_com_dados_no_lugar_dos_marcadores(alunos):
    esperados = [
        "Interessada(o): Maria Silva Campos - 1034567",
        "E-mail: maria.silva@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática Aplicada - Mestrado",
        "A CCP-Matemática Aplicada aprovou na data de hoje",
        "Dados do evento",
        "Evento: Workshop de Topologia",
        "Período: 10 e 11 de março de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://www.ime.usp.br/eventos/topologia",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem aérea e uma diária de hospedagem.",
        "Endereço da(o) interessada(o)",
        "Rua do Anfiteatro, 181",
        "Complemento: Sala 214",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    faltando = [trecho for trecho in esperados if trecho not in alunos["texto"]]
    assert not faltando, f"trechos ausentes no ofício: {faltando}"


def test_oficio_do_docente_usa_verba_do_programa(docentes):
    texto = docentes["texto"]
    assert "Interessada(o): Maria Silva Campos" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática Aplicada" in texto
    assert "Mestrado" not in texto


def test_linhas_de_opcionais_vazios_saem_do_oficio(alunos):
    texto = _responder(alunos, link="", complemento="")
    assert "Interessada(o): Maria Silva Campos" in texto
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_formulario_vazio_pede_preencher_uma_vez(alunos):
    corpo = {prop: (0 if isinstance(valor, int) else "")
             for prop, valor in alunos["corpo"].items()}
    texto = _texto(cliente.post(alunos["rota"], =corpo))
    assert "Preencha todos os campos" in texto
    assert texto.count("Preencha todos os campos") == 1


def test_n_usp_com_letras(alunos):
    texto = _responder(alunos, n_usp="10a4567")
    assert "N. USP deve conter apenas números" in texto


def test_agencia_com_letras(alunos):
    texto = _responder(alunos, agencia="12a4")
    assert "Número da agência deve conter apenas números" in texto


def test_valor_solicitado_zero(alunos):
    prop = alunos["onde"].get("valor")
    assert prop is not None, "campo de valor ausente do corpo da requisição"
    atual = alunos["corpo"][prop]
    nulo = 0 if isinstance(atual, int) else ("R$ 0,00" if "R$" in str(atual) else "0")
    texto = _responder(alunos, valor=nulo)
    assert "Valor solicitado deve ser maior que 0" in texto


def test_email_sem_arroba(alunos):
    texto = _responder(alunos, email="maria.silva")
    assert "E-mail inválido" in texto


def test_cpf_fora_do_formato(alunos):
    atual = str(alunos["corpo"][alunos["onde"]["cpf"]])
    fora = "1234567890" if "-" in atual else "123.456.789-09"
    texto = _responder(alunos, cpf=fora)
    assert "CPF deve estar no formato 000.000.000-00" in texto


def test_cpf_com_digitos_verificadores_errados(alunos):
    atual = str(alunos["corpo"][alunos["onde"]["cpf"]])
    errado = "123.456.789-11" if "-" in atual else "12345678911"
    texto = _responder(alunos, cpf=errado)
    assert "CPF inválido" in texto


def test_cep_fora_do_formato(alunos):
    atual = str(alunos["corpo"][alunos["onde"]["cep"]])
    fora = "05508090" if "-" in atual else "05508-090"
    texto = _responder(alunos, cep=fora)
    assert "CEP deve estar no formato 00000-000" in texto


def test_data_fora_do_formato(alunos):
    atual = str(alunos["corpo"][alunos["onde"]["data_nascimento"]])
    fora = "01021980" if "/" in atual else "01/02/1980"
    texto = _responder(alunos, data_nascimento=fora)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto


def test_data_que_nao_existe(alunos):
    atual = str(alunos["corpo"][alunos["onde"]["data_nascimento"]])
    ruim = "31/02/1980" if "/" in atual else "31021980"
    texto = _responder(alunos, data_nascimento=ruim)
    assert "Data de nascimento inválida" in texto


def test_varios_erros_aparecem_juntos(alunos):
    atual = str(alunos["corpo"][alunos["onde"]["cpf"]])
    fora = "1234567890" if "-" in atual else "123.456.789-09"
    texto = _responder(alunos, n_usp="10a4567", agencia="12a4",
                       email="maria.silva", cpf=fora)
    for mensagem in (
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
    ):
        assert mensagem in texto
