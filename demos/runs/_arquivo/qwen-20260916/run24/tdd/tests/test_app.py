from fastapi.testclient import TestClient

from conftest import BASE


def _body_alunos(**overrides):
    base = {
        "aba": "alunos",
        "nome": "Maria Silva",
        "nusp": "1234567",
        "programa": "Matemática",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Columbus Conference",
        "periodo": "01/07/2025 a 05/07/2025",
        "cidade_evento": "Columbus",
        "estado_evento": "Ohio",
        "pais_evento": "Estados Unidos",
        "link_evento": "https://columbus.org/2025",
        "valor": "R$ 1.500,00",
        "detalhamento": "Participação com apresentação de pôster.",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "012.345.678-90",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    base.update(overrides)
    return base


def _body_docentes(**overrides):
    base = _body_alunos()
    del base["nivel"]
    del base["tipo_auxilio"]
    base["aba"] = "docentes"
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Servir os arquivos estáticos e a página inicial
# ---------------------------------------------------------------------------


def test_pagina_principal_responde(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_arquivos_estaticos_existem_na_raiz():
    import os

    for nome in ("index.html", "style.css", "app.js", os.path.join("assets", "usp-logo.png")):
        assert os.path.isfile(os.path.join(BASE, nome)), nome


def test_pagina_carrega_css_e_js_locais(client):
    html = client.get("/").text
    assert "style.css" in html
    assert "app.js" in html
    # sem fonte remota / CDN: nenhuma url http(s) de recurso externo no HTML
    assert "http://" not in html and "https://" not in html
    css = client.get("/style.css").text
    assert "@import" not in css
    assert "http://" not in css and "https://" not in css


def test_assets_disponiveis(client):
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Conteúdo textual do index.html (contrato de rótulos / abas / placeholder)
# ---------------------------------------------------------------------------


def _html():
    import os

    with open(os.path.join(BASE, "index.html"), encoding="utf-8") as f:
        return f.read()


def _js():
    import os

    with open(os.path.join(BASE, "app.js"), encoding="utf-8") as f:
        return f.read()


def _css():
    import os

    with open(os.path.join(BASE, "style.css"), encoding="utf-8") as f:
        return f.read()


def _rotulos_exigidos():
    return {
        # abas
        "ALUNOS",
        "DOCENTES",
        "Enviar solicitação",
        # títulos dos blocos
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        # solicitante e evento
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
        # endereço
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        # pagamento
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
        # opções de NÍVEL
        "Mestrado",
        "Doutorado",
        # opções de TIPO DE AUXÍLIO
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        # opções de IRÁ APRESENTAR
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    }


def test_html_contem_todos_os_rotulos(client):
    html = client.get("/").text
    faltando = [r for r in _rotulos_exigidos() if r not in html]
    assert not faltando, faltando


def test_html_nao_menciona_brasao_ou_escudo():
    html = _html().lower()
    assert "bras" not in html
    assert "escudo" not in html


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------


def test_aba_alunos_ativa_inicialmente():
    import re

    html = _html()
    i_al = html.find("ALUNOS")
    i_do = html.find("DOCENTES")
    assert 0 <= i_al < i_do, "abas na ordem ALUNOS, DOCENTES"

    padrao = re.compile(r"<[^>]*>\s*ALUNOS\s*<", re.IGNORECASE)
    alvo = None
    for m in padrao.finditer(html):
        # pega a tag que envolve o texto ALUNOS
        abertura = html.rfind("<", 0, m.start())
        alvo = html[abertura:m.end()]
        break
    assert alvo is not None
    assert "active" in alvo.lower()


# ---------------------------------------------------------------------------
# Validação no backend - POST /solicitacao
# ---------------------------------------------------------------------------


def _esperado_erros(client, body):
    resp = client.post("/solicitacao", json=body)
    assert resp.status_code == 200, resp.status_code
    return resp.json().get("erros", [])


def _tem_erro(client, body, msg):
    return msg in _esperado_erros(client, body)


def test_envio_valido_sem_erros(client):
    erros = _esperado_erros(client, _body_alunos())
    assert erros == [], erros


def test_campo_obrigatorio_vazio(client):
    assert _tem_erro(client, _body_alunos(nome=""), "Preencha todos os campos")


def test_unicamente_campos_opcionais_podem_vazar(client):
    # somente o link do evento opcional vazio => sem erros
    assert _esperado_erros(client, _body_alunos(link_evento="")) == []
    assert _esperado_erros(client, _body_alunos(complemento="")) == []


def test_nusp_apenas_digitos(client):
    assert _tem_erro(client, _body_alunos(nusp="12A45"), "N. USP deve conter apenas números")


def test_agencia_apenas_digitos(client):
    assert _tem_erro(client, _body_alunos(agencia="12A4"), "Número da agência deve conter apenas números")


def test_valor_deve_ser_maior_que_zero(client):
    assert _tem_erro(client, _body_alunos(valor=""), "Valor solicitado deve ser maior que 0")
    assert _tem_erro(client, _body_alunos(valor="0"), "Valor solicitado deve ser maior que 0")
    assert _tem_erro(client, _body_alunos(valor="-50"), "Valor solicitado deve ser maior que 0")


def test_email_invalido(client):
    assert _tem_erro(client, _body_alunos(email="maria"), "E-mail inválido")
    assert _tem_erro(client, _body_alunos(email="maria@"), "E-mail inválido")


def test_cpf_formato(client):
    assert _tem_erro(client, _body_alunos(cpf="01234567890"), "CPF deve estar no formato 000.000.000-00")


def test_cpf_digitos_verificadores(client):
    # formato correto mas dígitos verificadores inválidos
    assert _tem_erro(client, _body_alunos(cpf="123.456.789-11"), "CPF inválido")


def test_cep_formato(client):
    assert _tem_erro(client, _body_alunos(cep="05508090"), "CEP deve estar no formato 00000-000")


def test_data_formato(client):
    assert _tem_erro(client, _body_alunos(data_nascimento="1-2-1980"), "Data de nascimento deve estar no formato dd/mm/aaaa")


def test_data_inexistente(client):
    assert _tem_erro(client, _body_alunos(data_nascimento="31/02/1980"), "Data de nascimento inválida")
    assert _tem_erro(client, _body_alunos(data_nascimento="01/13/1980"), "Data de nascimento inválida")


def test_abas_tem_mesmos_campos_excecoes(client):
    # aba docentes valida sem NÍVEL e TIPO DE AUXÍLIO
    assert _esperado_erros(client, _body_docentes()) == []


# ---------------------------------------------------------------------------
# Ofício gerado
# ---------------------------------------------------------------------------


def _oficio(client, body):
    resp = client.post("/solicitacao", json=body)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados.get("oficio"), dados
    return dados["oficio"]


def test_oficio_aluno_conteudo(client):
    of = _oficio(client, _body_alunos())
    assert "Maria Silva - 1234567" in of
    assert "E-mail: maria@ime.usp.br" in of
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in of
    assert "Programa: Matemática - Doutorado" in of
    assert "Evento: Columbus Conference" in of
    assert "Link do evento: https://columbus.org/2025" in of
    assert "Valor solicitado: R$ 1.500,00" in of
    assert "Complemento:" not in of  # vazio -> linha some
    assert "Rua do Matão, 1010" in of
    assert "CPF: 012.345.678-90" in of
    assert "Encaminhe-se ao Serviço Financeiro para providências." in of


def test_oficio_docente_linhas_diferentes(client):
    of = _oficio(client, _body_docentes())
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in of
    assert "Programa: Matemática\n" in of or of.splitlines()[4].strip() == "Programa: Matemática"


def test_oficio_sem_erro_quando_obrigatorios(client):
    resp = client.post("/solicitacao", json=_body_alunos(nome=""))
    dados = resp.json()
    assert "oficio" not in dados or not dados["oficio"]


# ---------------------------------------------------------------------------
# Comportamento de tela (app.js) - as quatro máscaras e troca de abas
# ---------------------------------------------------------------------------


def test_js_contem_funcoes_de_formatacao():
    js = _js()
    assert "function formatCpf" in js
    assert "function formatCep" in js
    assert "function formatData" in js
    assert "function formatValor" in js


def _extrair_funcao(nome):
    """Extrai a definição de uma função de nível de topo `function nome(...) {...}`
    de app.js, casando chaves balanceadas. Retorna o texto completo da definição."""
    js = _js()
    inicio = js.index("function %s" % nome)
    i = js.index("{", inicio)
    fim = js.index("(", inicio)
    fim = js.index(")", fim)
    i = js.index("{", fim)
    nivel = 0
    j = i
    while j < len(js):
        if js[j] == "{":
            nivel += 1
        elif js[j] == "}":
            nivel -= 1
            if nivel == 0:
                break
        j += 1
    return js[inicio : j + 1]


def _exec_funcao(nome, args):
    """Executa a função nomeada de app.js num subprocesso python (sem dependências
    externas) e retorna o valor devolvido."""
    import json
    import subprocess
    import sys

    fonte = _extrair_funcao(nome)
    programa = fonte + "\nimport sys, json\nprint(json.dumps(%s(*json.loads(sys.argv[1]))))\n" % nome
    proc = subprocess.run(
        [sys.executable, "-c", programa, json.dumps(args)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_format_cpf():
    assert _exec_funcao("formatCpf", ["12345678909"]) == "123.456.789-09"
    assert _exec_funcao("formatCpf", ["05508090"]) == "055.080-9005"  # truncamento/colagem não exigida; só valida 11 dígitos


def test_format_cep():
    assert _exec_funcao("formatCep", ["05508090"]) == "05508-090"


def test_format_data():
    assert _exec_funcao("formatData", ["01021980"]) == "01/02/1980"


def test_format_valor():
    assert _exec_funcao("formatValor", ["1500"]) == "R$ 15,00"
    assert _exec_funcao("formatValor", ["150000"]) == "R$ 1.500,00"
    assert _exec_funcao("formatValor", ["150000000"]) == "R$ 1.500.000,00"


# ---------------------------------------------------------------------------
# Aparência / layout (style.css)
# ---------------------------------------------------------------------------


def test_css_cores_da_instituicao():
    css = _css()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_css_fonte_sem_serifa():
    css = _css()
    assert "Open Sans" in css or "sans-serif" in css


def test_css_organiza_campos_em_multiplas_colunas():
    css = _css()
    assert ("grid" in css) or ("flex" in css)


def test_css_mascara_ativa_aba_distinta():
    css = _css()
    assert ".active" in css
