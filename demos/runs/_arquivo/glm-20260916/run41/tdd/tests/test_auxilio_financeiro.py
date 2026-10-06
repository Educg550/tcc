"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Cobre, pelo HTTP servido pela aplicação FastAPI:
- o frontend estático (index.html, style.css, app.js): abas, rótulos, blocos,
  placeholders, botão, título da confirmação, identidade visual e ausência de
  recursos baixados da rede;
- o backend: validação da solicitação (mensagens exatas do requisito) e geração
  do ofício para as abas ALUNOS e DOCENTES, inclusive a omissão das linhas dos
  campos opcionais deixados vazios.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Frontend: arquivos estáticos
# ---------------------------------------------------------------------------

LABELS = [
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

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]


def _flat(texto):
    return re.sub(r"\s+", " ", texto)


def _get(*caminhos):
    for caminho in caminhos:
        resp = client.get(caminho)
        if resp.status_code == 200:
            return resp
    return None


def _frontend():
    html = client.get("/").text
    js = _get("/app.js", "/static/app.js", "/js/app.js")
    return html, (js.text if js is not None else "")


def _css():
    css = _get("/style.css", "/static/style.css", "/css/style.css")
    return css.text if css is not None else ""


def test_pagina_e_arquivos_estaticos_servidos():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "html" in resp.headers.get("content-type", "")
    assert _get("/style.css", "/static/style.css") is not None, "style.css não servido"
    assert _get("/app.js", "/static/app.js") is not None, "app.js não servido"
    assert client.get("/assets/usp-logo.png").status_code == 200, "logotipo não servido"


def test_abas_alunos_e_docentes_nessa_ordem():
    html, js = _frontend()
    flat = _flat(html + "\n" + js)
    assert "ALUNOS" in flat and "DOCENTES" in flat, "abas ALUNOS e DOCENTES ausentes"
    assert flat.index("ALUNOS") < flat.index("DOCENTES"), "ALUNOS deve vir antes de DOCENTES"


def test_rotulos_e_blocos_exatos():
    html, js = _frontend()
    flat = _flat(html + "\n" + js)
    faltando = [rotulo for rotulo in LABELS + BLOCOS if rotulo not in flat]
    assert faltando == [], f"rótulos ausentes: {faltando}"


def test_formularios_com_botao_enviar_solicitacao():
    html, js = _frontend()
    flat = _flat(html + "\n" + js)
    assert "<form" in flat
    assert "Enviar solicitação" in flat


def test_todo_campo_tem_placeholder_de_exemplo():
    html, js = _frontend()
    codigo = html + "\n" + js
    valores = []
    for padrao in (
        r'placeholder\s*=\s*"([^"]*)"',
        r"placeholder\s*=\s*'([^']*)'",
        r'placeholder\s*:\s*"([^"]*)"',
        r"placeholder\s*:\s*'([^']*)'",
        r'''["']placeholder["']\s*,\s*["']([^"']*)["']''',
    ):
        valores += re.findall(padrao, codigo)
    assert len(valores) >= 28, "cada um dos 28 campos do formulário precisa de placeholder"
    rotulos = {_flat(rotulo).casefold() for rotulo in LABELS}
    for valor in valores:
        assert valor.strip(), "placeholder vazio"
        assert _flat(valor).strip().casefold() not in rotulos, (
            f"placeholder repete o rótulo: {valor!r}"
        )


def test_titulo_da_confirmacao():
    html, js = _frontend()
    assert "Solicitação registrada" in _flat(html + "\n" + js)


def test_identidade_visual_usp():
    html, js = _frontend()
    codigo = html + "\n" + js
    css = _css().lower()
    assert "usp-logo.png" in codigo, "logotipo da USP ausente"
    assert "Universidade de São Paulo" in _flat(codigo)
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css, f"cor institucional ausente: {cor}"
    assert "open sans" in css, "fonte Open Sans não referenciada"


def test_nenhum_recurso_baixado_da_rede():
    html, js = _frontend()
    for nome, codigo in (("index.html", html), ("style.css", _css()), ("app.js", js)):
        assert not re.search(r'''<script[^>]+src=['"]https?://''', codigo), nome
        assert not re.search(r'''<link[^>]+href=['"]https?://''', codigo), nome
        assert not re.search(r'''<img[^>]+src=['"]https?://''', codigo), nome
        assert not re.search(r'''@import\s+url\(\s*['"]?https?://''', codigo), nome
        assert "fonts.googleapis" not in codigo, nome


def test_so_o_logotipo_usp_aparece_na_pagina():
    html, js = _frontend()
    referencias = re.findall(r'''src=["']([^"']+)["']''', html + "\n" + js)
    referencias += re.findall(r'''url\(\s*['"]?([^'")]+)''', _css())
    imagens = [ref for ref in referencias if re.search(r"\.(png|jpe?g|svg|gif)$", ref, re.I)]
    assert imagens, "nenhuma imagem institucional referenciada"
    for imagem in imagens:
        assert imagem.endswith("usp-logo.png"), f"imagem indevida na página: {imagem}"


# ---------------------------------------------------------------------------
# Backend: validação e geração do ofício
# ---------------------------------------------------------------------------

OFICIO_MARCADOR = "Encaminhe-se ao Serviço Financeiro para providências."

NOME = "Maria Souza Silva"
N_USP = "1234567"
PROGRAMA = "Ciência da Computação"
EMAIL = "maria@usp.br"
EVENTO = "Simpósio de Computação"
PERIODO = "1 a 5 de julho de 2025"
CIDADE_EVENTO = "São Paulo"
ESTADO_EVENTO = "SP"
PAIS_EVENTO = "Brasil"
LINK_EVENTO = "https://www.ime.usp.br/evento"
DETALHAMENTO = "Passagem aérea e diárias"
LOGRADOURO = "Rua do Anfiteatro"
NUMERO = "181"
COMPLEMENTO = "Sala 222"
BAIRRO = "Butantã"
CIDADE = "São Paulo"
ESTADO = "SP"
RG_RNM = "12.345.678-9"
BANCO = "Banco do Brasil"
AGENCIA = "1234"
CONTA = "12345-6"

# O contrato exato do payload não é fixado pelo requisito; cada campo é enviado
# de uma vez sob todos os nomes de chave plausíveis (aliases + o próprio rótulo).
FIELDS = {
    "nome": ("nome_completo", "nome_completo_sem_abreviar", "nome",
             "NOME COMPLETO - SEM ABREVIAR"),
    "n_usp": ("n_usp", "num_usp", "numero_usp", "nusp", "N. USP"),
    "programa": ("programa", "PROGRAMA"),
    "nivel": ("nivel", "grau", "NÍVEL"),
    "tipo_auxilio": ("tipo_auxilio", "tipo_de_auxilio", "TIPO DE AUXÍLIO"),
    "email": ("email", "e_mail", "E-MAIL"),
    "nome_evento": ("nome_evento", "nome_do_evento", "evento",
                    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
    "periodo": ("periodo_evento", "periodo_do_evento", "periodo",
                "PERÍODO DO EVENTO, EXAME OU DEFESA"),
    "cidade_evento": ("cidade_evento", "cidade_do_evento",
                      "CIDADE DO EVENTO, EXAME OU DEFESA"),
    "estado_evento": ("estado_evento", "estado_do_evento",
                      "ESTADO DO EVENTO, EXAME OU DEFESA"),
    "pais_evento": ("pais_evento", "pais_do_evento",
                    "PAÍS DO EVENTO, EXAME OU DEFESA"),
    "link_evento": ("link_evento", "link_do_evento", "link", "url_evento",
                    "LINK DO EVENTO, EXAME OU DEFESA"),
    "valor": ("valor_solicitado", "valor", "VALOR SOLICITADO (R$)"),
    "detalhamento": ("detalhamento", "detalhamento_do_pedido", "DETALHAMENTO DO PEDIDO"),
    "apresentacao": ("apresentacao", "apresentacao_trabalho", "tipo_apresentacao",
                     "ira_apresentar_trabalho",
                     "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
    "data_nascimento": ("data_nascimento", "data_de_nascimento", "DATA DE NASCIMENTO"),
    "logradouro": ("logradouro", "endereco", "LOGRADOURO"),
    "numero": ("numero", "numero_endereco", "NUMERO"),
    "complemento": ("complemento", "COMPLEMENTO"),
    "bairro": ("bairro", "BAIRRO"),
    "cep": ("cep", "CEP"),
    "cidade": ("cidade", "CIDADE"),
    "estado": ("estado", "uf", "ESTADO"),
    "cpf": ("cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
    "rg": ("rg_rnm", "rg", "rnm", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
    "banco": ("nome_do_banco", "nome_banco", "banco", "NOME DO BANCO"),
    "agencia": ("numero_da_agencia", "numero_agencia", "agencia", "NÚMERO DA AGÊNCIA"),
    "conta": ("numero_da_conta", "numero_conta", "conta", "NÚMERO DA CONTA"),
}

VALORES = {
    "nome": NOME,
    "n_usp": N_USP,
    "programa": PROGRAMA,
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": EMAIL,
    "nome_evento": EVENTO,
    "periodo": PERIODO,
    "cidade_evento": CIDADE_EVENTO,
    "estado_evento": ESTADO_EVENTO,
    "pais_evento": PAIS_EVENTO,
    "link_evento": LINK_EVENTO,
    "valor": "@VALOR@",
    "detalhamento": DETALHAMENTO,
    "apresentacao": "Pôster",
    "data_nascimento": "@DATA@",
    "logradouro": LOGRADOURO,
    "numero": NUMERO,
    "complemento": COMPLEMENTO,
    "bairro": BAIRRO,
    "cep": "@CEP@",
    "cidade": CIDADE,
    "estado": ESTADO,
    "cpf": "@CPF@",
    "rg": RG_RNM,
    "banco": BANCO,
    "agencia": AGENCIA,
    "conta": CONTA,
}

# Os campos formatados podem chegar ao backend já formatados (como a tela os
# mostra ao perder o foco) ou como só dígitos; o ofício traz a forma formatada.
FORMAT_COMBOS = [
    {"valor": "R$ 1.500,00", "data": "01/02/1980", "cep": "05508-090",
     "cpf": "123.456.789-09"},
    {"valor": "150000", "data": "01021980", "cep": "05508090", "cpf": "12345678909"},
    {"valor": "1500.00", "data": "01/02/1980", "cep": "05508-090",
     "cpf": "123.456.789-09"},
]

DISC_ALUNO = [
    {}, {"aba": "alunos"}, {"tipo": "aluno"}, {"tipo_solicitacao": "aluno"},
    {"perfil": "aluno"}, {"categoria": "aluno"},
]
DISC_DOCENTE = [
    {}, {"aba": "docentes"}, {"tipo": "docente"}, {"tipo_solicitacao": "docente"},
    {"perfil": "docente"}, {"categoria": "docente"},
]

FALLBACK_PATHS = [
    "/solicitacao", "/api/solicitacao", "/solicitar", "/api/solicitar",
    "/solicitacoes", "/enviar", "/submit", "/validar", "/oficio", "/processar",
    "/solicitacao/alunos", "/solicitacao/docentes", "/auxilio",
    "/auxilio-financeiro",
]

_POST_PATHS = None
_KNOWN_ENDPOINTS = None


def _payload(combo, remover=(), em_branco=(), extra=None):
    formatados = {
        "@VALOR@": combo["valor"],
        "@DATA@": combo["data"],
        "@CEP@": combo["cep"],
        "@CPF@": combo["cpf"],
    }
    dados = {}
    for campo, valor in VALORES.items():
        if campo in remover:
            continue
        valor = formatados.get(valor, valor)
        for chave in FIELDS[campo]:
            dados[chave] = valor
    for chave in em_branco:
        dados[chave] = ""
    if extra:
        dados.update(extra)
    return dados


def _walk(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for item in valor.values():
            yield from _walk(item)
    elif isinstance(valor, (list, tuple)):
        for item in valor:
            yield from _walk(item)


def _texto(resp):
    try:
        dados = resp.()
    except Exception:
        return resp.text
    return "\n".join(_walk(dados))


def _post_paths():
    global _POST_PATHS
    if _POST_PATHS is None:
        caminhos = []
        try:
            spec = client.get("/openapi.").()
            for caminho, metodos in (spec.get("paths") or {}).items():
                if isinstance(metodos, dict) and "post" in metodos:
                    caminhos.append(caminho)
        except Exception:
            pass
        for candidato in FALLBACK_PATHS:
            if candidato not in caminhos:
                caminhos.append(candidato)
        _POST_PATHS = caminhos
    return _POST_PATHS


def _post_one(caminho, payload):
    respostas = [client.post(caminho, =payload)]
    if respostas[0].status_code == 422:
        respostas.append(client.post(caminho, data=payload))
    return respostas


def _endpoints_de_processamento():
    global _KNOWN_ENDPOINTS
    if _KNOWN_ENDPOINTS is not None:
        return _KNOWN_ENDPOINTS
    encontrados = []
    for combo in FORMAT_COMBOS:
        payload = _payload(combo)
        for caminho in _post_paths():
            if caminho in encontrados:
                continue
            if any(OFICIO_MARCADOR in _texto(r) for r in _post_one(caminho, payload)):
                encontrados.append(caminho)
        if encontrados:
            break
    _KNOWN_ENDPOINTS = encontrados
    return _KNOWN_ENDPOINTS


def _send(payload):
    conhecidos = _endpoints_de_processamento()
    outros = [c for c in _post_paths() if c not in conhecidos]
    respostas = []
    for caminho in conhecidos + outros:
        respostas.extend(_post_one(caminho, payload))
    return respostas


def _find(payloads, grupos, proibidos=()):
    for payload in payloads:
        for resp in _send(payload):
            texto = _texto(resp)
            if not all(any(alt in texto for alt in grupo) for grupo in grupos):
                continue
            if not any(p in texto for p in proibidos):
                return texto
    return None


def _assert_erro(payloads, *mensagens):
    texto = _find(payloads, [[m] for m in mensagens], proibidos=(OFICIO_MARCADOR,))
    assert texto is not None, f"nenhuma resposta trouxe as mensagens {list(mensagens)}"


def _erro_payloads(campo, valores):
    payloads = []
    for valor in valores:
        dados = _payload(FORMAT_COMBOS[0])
        for chave in FIELDS[campo]:
            dados[chave] = valor
        payloads.append(dados)
    return payloads


def _aluno_payloads():
    return [_payload(combo, extra=disc)
            for combo in FORMAT_COMBOS for disc in DISC_ALUNO]


def _docente_payloads():
    return [_payload(combo, remover=("nivel", "tipo_auxilio"), extra=disc)
            for combo in FORMAT_COMBOS for disc in DISC_DOCENTE]


def _sem_opcionais_payloads():
    chaves_opcionais = FIELDS["link_evento"] + FIELDS["complemento"]
    payloads = []
    for combo in FORMAT_COMBOS:
        payloads.append(_payload(combo, remover=("link_evento", "complemento")))
        payloads.append(_payload(combo, em_branco=chaves_opcionais))
    return payloads


def _grupos_aluno():
    return [
        [f"Interessada(o): {NOME} - {N_USP}"],
        [f"E-mail: {EMAIL}"],
        ["Assunto: Solicitação de Auxílio Financeiro - Participação em evento"],
        [f"Programa: {PROGRAMA} - Mestrado"],
        [f"A CCP-{PROGRAMA} aprovou"],
        ["Dados do evento"],
        [f"Evento: {EVENTO}"],
        [f"Período: {PERIODO}"],
        [f"Local: {CIDADE_EVENTO} - {ESTADO_EVENTO} - {PAIS_EVENTO}"],
        [f"Link do evento: {LINK_EVENTO}"],
        ["Apresentação de trabalho: Pôster", "Apresentação de trabalho: Poster"],
        ["Valor solicitado: R$ 1.500,00"],
        [f"Detalhamento: {DETALHAMENTO}"],
        ["Endereço da(o) interessada(o)"],
        [f"{LOGRADOURO}, {NUMERO}"],
        [f"Complemento: {COMPLEMENTO}"],
        ["CEP: 05508-090"],
        [f"{BAIRRO}, {CIDADE} - {ESTADO}"],
        ["Dados para pagamento"],
        ["Data de nascimento: 01/02/1980"],
        ["CPF: 123.456.789-09"],
        [f"RG / RNM: {RG_RNM}"],
        [f"Banco: {BANCO}"],
        [f"Agência: {AGENCIA}"],
        [f"Conta: {CONTA}"],
        [OFICIO_MARCADOR],
    ]


def _grupos_aluno_sem_opcionais():
    return [
        grupo for grupo in _grupos_aluno()
        if not grupo[0].startswith(("Link do evento:", "Complemento:"))
    ]


def _grupos_docente():
    return [
        [f"Interessada(o): {NOME} - {N_USP}"],
        [f"E-mail: {EMAIL}"],
        ["Assunto: Solicitação de Auxílio Financeiro - Verba do programa"],
        [f"Programa: {PROGRAMA}"],
        [f"A CCP-{PROGRAMA} aprovou"],
        [f"Local: {CIDADE_EVENTO} - {ESTADO_EVENTO} - {PAIS_EVENTO}"],
        ["Valor solicitado: R$ 1.500,00"],
        ["CEP: 05508-090"],
        ["Data de nascimento: 01/02/1980"],
        ["CPF: 123.456.789-09"],
        [OFICIO_MARCADOR],
    ]


def test_oficio_da_aba_alunos():
    texto = _find(_aluno_payloads(), _grupos_aluno())
    assert texto is not None, "backend não gerou o ofício do aluno com dados válidos"


def test_oficio_da_aba_docentes():
    texto = _find(_docente_payloads(), _grupos_docente(),
                  proibidos=("Mestrado", "Participação em evento"))
    assert texto is not None, "backend não gerou o ofício do docente"


def test_oficio_omite_linhas_de_opcionais_vazios():
    texto = _find(_sem_opcionais_payloads(), _grupos_aluno_sem_opcionais(),
                  proibidos=("Link do evento:", "Complemento:"))
    assert texto is not None, "ofício deveria omitir as linhas de link e complemento vazios"


def test_erro_campos_obrigatorios_vazios():
    completo_em_branco = {chave: "" for chave in _payload(FORMAT_COMBOS[0])}
    for payload in ({}, completo_em_branco):
        for resp in _send(payload):
            texto = _texto(resp)
            if "Preencha todos os campos" in texto:
                assert texto.count("Preencha todos os campos") == 1, (
                    "a mensagem de campos vazios deve aparecer uma única vez"
                )
                assert OFICIO_MARCADOR not in texto
                return
    pytest.fail("mensagem 'Preencha todos os campos' não retornada")


def test_erro_n_usp_nao_numerico():
    _assert_erro(_erro_payloads("n_usp", ["12a45b7"]),
                 "N. USP deve conter apenas números")


def test_erro_agencia_nao_numerica():
    _assert_erro(_erro_payloads("agencia", ["12a4"]),
                 "Número da agência deve conter apenas números")


def test_erro_valor_menor_ou_igual_a_zero():
    _assert_erro(_erro_payloads("valor", ["0", "00", "R$ 0,00", "0.00"]),
                 "Valor solicitado deve ser maior que 0")


def test_erro_email_invalido():
    _assert_erro(_erro_payloads("email", ["maria.usp.br"]), "E-mail inválido")


def test_erro_formato_do_cpf():
    _assert_erro(_erro_payloads("cpf", ["123456789", "123.456.789"]),
                 "CPF deve estar no formato 000.000.000-00")


def test_erro_digitos_verificadores_do_cpf():
    _assert_erro(_erro_payloads("cpf", ["111.444.777-34", "11144477734"]),
                 "CPF inválido")


def test_erro_formato_do_cep():
    _assert_erro(_erro_payloads("cep", ["0550809", "05508-09", "055080900"]),
                 "CEP deve estar no formato 00000-000")


def test_erro_formato_da_data_de_nascimento():
    _assert_erro(_erro_payloads("data_nascimento", ["01-02-1980", "1980-02-01", "0102198"]),
                 "Data de nascimento deve estar no formato dd/mm/aaaa")


def test_erro_data_de_nascimento_inexistente():
    _assert_erro(
        _erro_payloads("data_nascimento",
                       ["31/02/1980", "31021980", "15/13/1980", "15131980"]),
        "Data de nascimento inválida",
    )


def test_erro_multiplas_mensagens_juntas():
    dados = _payload(FORMAT_COMBOS[0])
    for chave in FIELDS["n_usp"]:
        dados[chave] = "12a45b7"
    for chave in FIELDS["email"]:
        dados[chave] = "maria.usp.br"
    for chave in FIELDS["agencia"]:
        dados[chave] = "12a4"
    _assert_erro([dados],
                 "N. USP deve conter apenas números",
                 "E-mail inválido",
                 "Número da agência deve conter apenas números")
