"""Testes da página do formulário de auxílio financeiro do IME-USP.

O requisito diz: FastAPI, arquivos estáticos servidos por ele, e uma tela
única com duas abas (`ALUNOS` e `DOCENTES`). Estes testes verificam, no HTML
estático servido pela aplicação, tudo o que o requisito descreve como
comportamento visível: rótulos, abas, blocos, placeholders, formatadores,
validação e o ofício gerado.
"""

import pathlib
import re
import sys

# Caminho até a raiz do projeto (o mesmo nível em que pytest roda).
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _le(nome):
    p = RAIZ / nome
    assert p.exists(), f"{nome} inexistente: não há aplicação para testar"
    return p.read_text(encoding="utf-8")


def _html():
    return _le("index.html")


def _css():
    return _le("style.css")


def _js():
    return _le("app.js")


def _script(q):
    m = re.search(r"<script\b[^>]*>.*?</script>", q, re.I | re.S)
    return m.group(0) if m else ""


def _comentarios(q):
    return re.findall(r"<!--(.*?)-->", q, re.S)


def _brasoes(q):
    return re.findall(r"<img\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)", q, re.I)


def _id_existe(q, id_, tag=None, tipo=None):
    m = re.search(r"<([a-zA-Z0-9-]+)\b[^>]*\bid\s*=\s*[\"']%s[\"']" % re.escape(id_), q, re.I)
    assert m, f"id {id_} não encontrado"
    return m.group(0)


def _opcoes(q, id_):
    el = _id_existe(q, id_)
    return re.findall(r"<option\b[^>]*>(.*?)</option>", el, re.I | re.S)


def _rotulo(q, campo):
    m = re.search(r"<label\b[^>]*>(.*?)</label>", q, re.I | re.S)
    # localizar label por for
    for lab in re.finditer(r"<label\b([^>]*)>(.*?)</label>", q, re.I | re.S):
        if re.search(r"\bfor\s*=\s*[\"']%s[\"']" % re.escape(campo), lab.group(1), re.I):
            return re.sub(r"<[^>]+>", "", lab.group(2)).strip()
    return None


def _titulo_de(q, id_):
    el = _id_existe(q, id_)
    m = re.search(r"aria-labelledby\s*=\s*[\"']([^\"']+)[\"']", el, re.I)
    assert m, f"{id_} sem aria-labelledby ligando a bloco"
    titulo = _id_existe(q, m.group(1))
    m = re.search(r">\s*([^<>]*?)\s*<", titulo, re.S)
    return m.group(1) if m else ""


def _lid(q, id_):
    m = re.search(r"<label\b[^>]*\bid\s*=\s*[\"']%s[\"']" % re.escape(id_), q, re.I)
    assert m, f"label {id_} não encontrada"
    return m.group(0)


def _ligado_a(q, campo, rotulo_id):
    m = re.search(r"<([a-zA-Z0-9-]+)\b[^>]*\bid\s*=\s*[\"']%s[\"']" % re.escape(campo), q, re.I)
    assert m, f"id {campo} não encontrado"
    assert re.search(r"\bfor\s*=\s*[\"']%s[\"']" % re.escape(campo), _lid(q, rotulo_id), re.I), f"{campo} não ligado a {rotulo_id}"


# ---------- abas ----------


def test_pagina_existe_e_h2():
    r = app_get("/index.html")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert r"<h1" in r.text and r"USP - Pós-Graduação" in r.text


def test_css_e_js_existentes_e_texto():
    r = app_get("/style.css")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/css")
    assert r.text.strip() and ";" in r.text
    r = app_get("/app.js")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/javascript")
    assert r.text.strip()


def test_fonte_open_sans():
    r = app_get("/style.css")
    assert "Open Sans" in r.text


def test_aba_alunos_ativa_docentes_nao():
    q = _html()
    a = _lid(q, "rotulo-aba-alunos")
    d = _lid(q, "rotulo-aba-docentes")
    assert 'class="aba ativa"' in a
    assert "ativa" not in d
    assert re.search(r"aria-selected\s*=\s*[\"']true", a)
    assert re.search(r"aria-selected\s*=\s*[\"']false", d)


def test_rotulos_das_abas():
    q = _html()
    assert re.sub(r"<[^>]+>", "", re.search(r"<label[^>]*id=\"rotulo-aba-alunos\"[^>]*>(.*?)</label>", q, re.S).group(1)).strip() == "ALUNOS"
    assert re.sub(r"<[^>]+>", "", re.search(r"<label[^>]*id=\"rotulo-aba-docentes\"[^>]*>(.*?)</label>", q, re.S).group(1)).strip() == "DOCENTES"


def test_aba_alunos_primeiro_e_form_docentes_escondido():
    q = _html()
    m1 = re.search(r"id=\"rotulo-aba-alunos\"", q)
    m2 = re.search(r"id=\"rotulo-aba-docentes\"", q)
    assert m1 and m2 and m1.start() < m2.start()
    assert "hidden" in _id_existe(q, "form-docentes")


def test_algum_estilo_para_aba_ativa():
    c = _css()
    assert re.search(r"\.aba\b", c)


def test_radios_das_abas():
    q = _html()
    a = _id_existe(q, "aba-alunos", "input")
    d = _id_existe(q, "aba-docentes", "input")
    assert 'type="radio"' in a.lower()
    assert 'type="radio"' in d.lower()
    assert re.search(r"name\s*=\s*[\"']aba[\"']", a)
    assert re.search(r"name\s*=\s*[\"']aba[\"']", d)
    assert re.search(r"checked", a, re.I)
    assert not re.search(r"checked", d, re.I)


def test_evento_de_troca_de_aba_existe():
    j = _js()
    assert "aba-alunos" in j and "aba-docentes" in j
    assert re.search(r"change|click", j)


def test_radios_escondidos():
    c = _css()
    m = re.search(r"#aba-alunos\s*,\s*#aba-docentes\s*\{[^}]*display\s*:\s*none\s*;", c)
    assert m, "radios das abas devem estar escondidos"


# ---------- cabeçalho e identidade visual ----------


def test_cabecalho_institucional():
    q = _html()
    m = re.search(r"<header\b.*?</header>", q, re.I | re.S)
    assert m, "cabeçalho institucional inexistente"
    h = m.group(0)
    assert re.search(r"<img\b[^>]*\bsrc\s*=\s*[\"']assets/usp-logo\.png[\"']", h, re.I), "logotipo da USP ausente"
    assert "Universidade de São Paulo" in h
    m2 = re.search(r"<h2\b[^>]*>(.*?)</h2>", q, re.I | re.S)
    assert m2 and "Pós-Graduação" in m2.group(1)


def test_margem_ao_redor_do_logotipo():
    c = _css()
    assert re.search(r"\.logo-margem\s*\{[^}]*\bpadding\s*:\s*[^;]*em\s*;", c), "margem livre em `em` ao redor do logotipo"


def test_brasao_nao_aparece():
    q = _html()
    for src in _brasoes(q):
        low = src.lower()
        assert "brasao" not in low and "escudo" not in low and "shield" not in low, f"brasão indevido: {src}"
    for c in _comentarios(q):
        low = c.lower()
        assert "brasao" not in low and "escudo" not in low, f"brasão indevido: {c}"


def test_paleta_usp():
    c = _css()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in c, f"cor institucional {cor} ausente"


def test_sem_fonte_externa():
    q = _html()
    assert "@import" not in _css()
    for u in re.findall(r"https?://[^\s\"'<>]+", _css()):
        assert False, f"CSS não pode referenciar rede: {u}"


def test_layout_horizontal():
    c = _css()
    assert re.search(r"@media\s*\([^)]*min-width\s*:\s*\s*640px\s*\)", c), "layout de múltiplas colunas esperado"


def test_oficio_preserva_quebras():
    c = _css()
    assert re.search(r"\.oficio\s*\{[^}]*white-space\s*:\s*pre-line\s*;", c), "ofício deve preservar quebras de linha"


# ---------- blocos ----------

BLOCOS = (
    ("SOLICITANTE E EVENTO", "titulo-bloco-solicitante"),
    ("ENDEREÇO DO SOLICITANTE", "titulo-bloco-endereco"),
    ("INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO", "titulo-bloco-pagamento"),
)


def test_blocos_com_titulos_exatos_em_ambos_os_formularios():
    q = _html()
    for form_id in ("form-alunos", "form-docentes"):
        form = re.search(r"<form\b[^>]*id=\"%s\"[^>]*>.*?</form>" % form_id, q, re.I | re.S)
        assert form, f"formulário {form_id} inexistente"
        f = form.group(0)
        for texto, titulo_id in BLOCOS:
            m = re.search(r"<h3\b[^>]*id=\"%s\"[^>]*>\s*%s\s*</h3>" % (titulo_id, re.escape(texto)), f)
            assert m, f"{form_id}: título {texto!r} inexistente em h3#{titulo_id}"


def test_campos_ligados_ao_bloco():
    q = _html()
    for _t, tid in BLOCOS:
        for campo, rot in CAMPOS_BLOCO[tid]:
            _ligado_a(q, campo, rot)


def test_somente_h3_para_blocos():
    q = _html()
    n = len(re.findall(r"<h3\b", q, re.I))
    assert n == 6, "esperados 6 títulos de bloco (3 por formulário)"


# ---------- rótulos e campos ----------

CAMPOS_BLOCO = {
    "titulo-bloco-solicitante": (
        ("a-nome", "rotulo-a-nome"),
        ("a-nusp", "rotulo-a-nusp"),
        ("a-programa", "rotulo-a-programa"),
        ("a-nivel", "rotulo-a-nivel"),
        ("a-tipo", "rotulo-a-tipo"),
        ("a-email", "rotulo-a-email"),
        ("a-evento", "rotulo-a-evento"),
        ("a-periodo", "rotulo-a-periodo"),
        ("a-cidade-evento", "rotulo-a-cidade-evento"),
        ("a-estado-evento", "rotulo-a-estado-evento"),
        ("a-pais-evento", "rotulo-a-pais-evento"),
        ("a-link", "rotulo-a-link"),
        ("a-valor", "rotulo-a-valor"),
        ("a-detalhamento", "rotulo-a-detalhamento"),
        ("a-apresentacao", "rotulo-a-apresentacao"),
    ),
    "titulo-bloco-endereco": (
        ("a-nascimento", "rotulo-a-nascimento"),
        ("a-logradouro", "rotulo-a-logradouro"),
        ("a-numero", "rotulo-a-numero"),
        ("a-complemento", "rotulo-a-complemento"),
        ("a-bairro", "rotulo-a-bairro"),
        ("a-cep", "rotulo-a-cep"),
        ("a-cidade", "rotulo-a-cidade"),
        ("a-estado", "rotulo-a-estado"),
    ),
    "titulo-bloco-pagamento": (
        ("a-cpf", "rotulo-a-cpf"),
        ("a-rg", "rotulo-a-rg"),
        ("a-banco", "rotulo-a-banco"),
        ("a-agencia", "rotulo-a-agencia"),
        ("a-conta", "rotulo-a-conta"),
    ),
}

ROTULOS = {
    "a-nome": "NOME COMPLETO - SEM ABREVIAR",
    "a-nusp": "N. USP",
    "a-programa": "PROGRAMA",
    "a-nivel": "NÍVEL",
    "a-tipo": "TIPO DE AUXÍLIO",
    "a-email": "E-MAIL",
    "a-evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "a-periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "a-cidade-evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "a-estado-evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "a-pais-evento": "PAÍS DO EVENTO, EXAME OU DEFESA",
    "a-link": "LINK DO EVENTO, EXAME OU DEFESA",
    "a-valor": "VALOR SOLICITADO (R$)",
    "a-detalhamento": "DETALHAMENTO DO PEDIDO",
    "a-apresentacao": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "a-nascimento": "DATA DE NASCIMENTO",
    "a-logradouro": "LOGRADOURO",
    "a-numero": "NÚMERO",
    "a-complemento": "COMPLEMENTO",
    "a-bairro": "BAIRRO",
    "a-cep": "CEP",
    "a-cidade": "CIDADE",
    "a-estado": "ESTADO",
    "a-cpf": "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "a-rg": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "a-banco": "NOME DO BANCO",
    "a-agencia": "NÚMERO DA AGÊNCIA",
    "a-conta": "NÚMERO DA CONTA",
}

PREFIXOS = (
    "titulo-bloco-solicitante",
    "titulo-bloco-endereco",
    "titulo-bloco-pagamento",
)

OPCOES_NIVEL = ["Mestrado", "Doutorado"]
OPCOES_TIPO = ["Participação em evento", "Banca de exame ou defesa", "Outro"]
OPCOES_APRESENTACAO = ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]

CAMPOS_OPCIONAIS = ("a-link", "a-complemento")

PLACEHOLDERS = {
    "a-nome": "Maria da Silva Souza",
    "a-nusp": "12345678",
    "a-programa": "Matemática Aplicada",
    "a-nivel": "Mestrado",
    "a-tipo": "Banca de exame ou defesa",
    "a-email": "nome@usp.br",
    "a-evento": "Congresso Brasileiro de Matemática",
    "a-periodo": "10/03/2025 a 14/03/2025",
    "a-cidade-evento": "São Paulo",
    "a-estado-evento": "São Paulo",
    "a-pais-evento": "Brasil",
    "a-link": "https://www.example.com/evento",
    "a-valor": "1.500,00",
    "a-detalhamento": "Inscrição no evento",
    "a-apresentacao": "Apresentação oral",
    "a-nascimento": "01/02/1980",
    "a-logradouro": "Rua do Matão",
    "a-numero": "1010",
    "a-complemento": "Prédio 2, sala 12",
    "a-bairro": "Butantã",
    "a-cep": "05508-090",
    "a-cidade": "São Paulo",
    "a-estado": "São Paulo",
    "a-cpf": "123.456.789-09",
    "a-rg": "12.345.678-9",
    "a-banco": "Banco do Brasil",
    "a-agencia": "1234",
    "a-conta": "12345-6",
}


MAPEAMENTO_FORMS = {
    "alunos": "form-alunos",
    "docentes": "form-docentes",
}


def _prefixo(form):
    return "a-" if form == "alunos" else "d-"


def _form(q, nome):
    m = re.search(r"<form\b[^>]*id=\"%s\"[^>]*>.*?</form>" % MAPEAMENTO_FORMS[nome], q, re.I | re.S)
    assert m, f"formulário {nome} inexistente"
    return m.group(0)


def _rotulo_de(q, form, sufixo):
    pref = _prefixo(form)
    rot = "rotulo-" + pref + sufixo
    m = re.search(r"<label\b[^>]*id=\"%s\"[^>]*>(.*?)</label>" % rot, q, re.I | re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else None


def _campo(q, form, sufixo):
    pref = _prefixo(form)
    cid = pref + sufixo
    m = re.search(r"<(input|select|textarea)\b[^>]*\bid=\"%s\"[^>]*" % cid, q, re.I)
    return m.group(0) if m else None


def _form_html(nome):
    return _form(_html(), nome)


def _rotulo_html(q, form, sufixo):
    pref = _prefixo(form)
    rot = "rotulo-" + pref + sufixo
    m = re.search(r"<label\b[^>]*id=\"%s\"[^>]*>.*?</label>" % rot, q, re.I | re.S)
    return m.group(0) if m else None


def _rotulos_do_formulario(q, nome):
    pref = _prefixo(nome)
    out = {}
    for sufixo, texto in ROTULOS.items():
        r = _rotulo_de(q, nome, sufixo)
        if r is not None:
            out[texto] = sufixo
    return out


def test_rotulos_iguais_nas_duas_abas_exceto_excecoes():
    q = _html()
    ra = _rotulos_do_formulario(q, "alunos")
    rd = _rotulos_do_formulario(q, "docentes")
    esperado_a = set(ROTULOS.values())
    esperado_d = esperado_a - {ROTULOS["a-nivel"], ROTULOS["a-tipo"]}
    assert set(ra) == esperado_a, "rótulos da aba ALUNOS incorretos"
    assert set(rd) == esperado_d, "rótulos da aba DOCENTES incorretos"


def test_rotulos_exatos():
    q = _html()
    for nome in ("alunos", "docentes"):
        for sufixo, texto in ROTULOS.items():
            if nome == "docentes" and sufixo in ("a-nivel", "a-tipo"):
                continue
            assert _rotulo_de(q, nome, sufixo) == texto, f"{nome}/{sufixo}: rótulo incorreto"


def test_placeholders_sao_exemplos():
    q = _html()
    for nome in ("alunos", "docentes"):
        for sufixo in ROTULOS:
            if nome == "docentes" and sufixo in ("a-nivel", "a-tipo"):
                continue
            campo = _campo(q, nome, sufixo)
            assert campo is not None, f"{nome}/{sufixo}: campo inexistente"
            m = re.search(r"placeholder\s*=\s*[\"']([^\"']*)[\"']", campo)
            assert m, f"{nome}/{sufixo}: placeholder ausente"
            ph = m.group(1).strip()
            assert ph, f"{nome}/{sufixo}: placeholder vazio"
            texto = ROTULOS[sufixo]
            assert ph != texto, f"{nome}/{sufixo}: placeholder repete o rótulo"
            assert ph.lower() != texto.lower()
            if nome == "alunos":
                assert ph == PLACEHOLDERS[sufixo], f"{nome}/{sufixo}: placeholder não é exemplo"


def test_campos_obrigatorios_exceto_opcionais():
    q = _html()
    for nome in ("alunos", "docentes"):
        for sufixo in ROTULOS:
            if nome == "docentes" and sufixo in ("a-nivel", "a-tipo"):
                continue
            campo = _campo(q, nome, sufixo)
            requerido = sufixo not in CAMPOS_OPCIONAIS
            tem = "required" in campo.lower()
            assert tem == requerido, f"{nome}/{sufixo}: required deveria ser {requerido}"


def test_tipos_de_campo():
    q = _html()
    tipos = {
        "a-nusp": "text",
        "a-email": "email",
        "a-valor": "text",
        "a-detalhamento": "textarea",
        "a-nascimento": "text",
        "a-cep": "text",
        "a-cpf": "text",
        "a-agencia": "text",
    }
    for nome in ("alunos", "docentes"):
        for sufixo, tipo in tipos.items():
            campo = _campo(q, nome, sufixo)
            if tipo == "textarea":
                assert campo.lower().startswith("<textarea"), f"{nome}/{sufixo}: devia ser textarea"
            else:
                m = re.search(r"type\s*=\s*[\"']([^\"']+)[\"']", campo, re.I)
                assert m and m.group(1).lower() == tipo, f"{nome}/{sufixo}: type incorreto"


def test_selecoes():
    q = _html()
    for nome, casos in (("alunos", (("nivel", OPCOES_NIVEL), ("tipo", OPCOES_TIPO), ("apresentacao", OPCOES_APRESENTACAO))), ("docentes", (("apresentacao", OPCOES_APRESENTACAO),))):
        for sufixo, esperado in casos:
            pref = _prefixo(nome)
            campo = _campo(q, nome, sufixo)
            assert campo is not None and campo.lower().startswith("<select"), f"{nome}/{sufixo}: devia ser select"
            achado = [o.strip() for o in re.findall(r"<option\b[^>]*>(.*?)</option>", campo, re.I | re.S)]
            assert achado == esperado, f"{nome}/{sufixo}: opções incorretas"


def test_campos_formataveis_ligam_formatter():
    q = _html()
    j = _js()
    for sufixo in ("valor", "cpf", "cep", "nascimento"):
        for nome in ("alunos", "docentes"):
            pref = _prefixo(nome)
            cid = pref + sufixo
            assert cid in j, f"app.js não referencia {cid}"
        assert sufixo in j
    assert "formatter" in j or "blur" in j or "change" in j


def test_mensagens_de_erro_exatas_no_js():
    j = _js()
    for msg in (
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        "CPF inválido",
        "Data de nascimento inválida",
    ):
        assert msg in j, f"mensagem ausente: {msg}"


def test_formularios_nao_enviam_native():
    q = _html()
    for nome in ("alunos", "docentes"):
        form = _form(q, nome)
        assert re.search(r"action\s*=", form, re.I) is None, f"{nome}: form não deve usar action nativo"


def test_post_de_alunos_retorna_oficio():
    r = app_get("/index.html")
    q = r.text
    _ = q
    payload = {
        "nome_completo": "Maria da Silva Souza",
        "n_usp": "12345678",
        "programa": "Matemática Aplicada",
        "nivel": "Doutorado",
        "tipo_auxilio": "Banca de exame ou defesa",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Brasileiro de Matemática",
        "periodo": "10/03/2025 a 14/03/2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "São Paulo",
        "pais_evento": "Brasil",
        "link": "https://www.example.com/cbm",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição e passagem",
        "apresentacao": "Pôster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "São Paulo",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    resp = app_post("/api/alunos", payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    oficio = data["oficio"]
    assert "Interessada(o): Maria da Silva Souza - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Banca de exame ou defesa" in oficio
    assert "Programa: Matemática Aplicada - Doutorado" in oficio
    assert "A CCP-Matemática Aplicada aprovou" in oficio
    assert "Evento: Congresso Brasileiro de Matemática" in oficio
    assert "Período: 10/03/2025 a 14/03/2025" in oficio
    assert "Local: São Paulo - São Paulo - Brasil" in oficio
    assert "Link do evento: https://www.example.com/cbm" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e passagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - São Paulo" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "Complemento:" not in oficio


def test_post_de_docentes_usa_verba_do_programa():
    payload = {
        "nome_completo": "João de Barros",
        "n_usp": "87654321",
        "programa": "Matemática",
        "email": "joao@ime.usp.br",
        "evento": "Seminário de Álgebra",
        "periodo": "05/05/2025",
        "cidade_evento": "Campinas",
        "estado_evento": "São Paulo",
        "pais_evento": "Brasil",
        "link": "",
        "valor": "R$ 300,00",
        "detalhamento": "Passagem",
        "apresentacao": "Não irá apresentar trabalho",
        "nascimento": "03/04/1975",
        "logradouro": "Rua XV de Novembro",
        "numero": "100",
        "complemento": "",
        "bairro": "Centro",
        "cep": "13010-000",
        "cidade": "Campinas",
        "estado": "São Paulo",
        "cpf": "529.982.247-25",
        "rg": "34.567.890-1",
        "banco": "Itaú",
        "agencia": "0999",
        "conta": "98765-4",
    }
    resp = app_post("/api/docentes", payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    oficio = data["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_post_com_erro_retorna_todas_as_mensagens():
    payload = {
        "nome_completo": "",
        "n_usp": "12a",
        "programa": "",
        "nivel": "Mestrado",
        "tipo_auxilio": "Outro",
        "email": "sem-arroba",
        "evento": "",
        "periodo": "",
        "cidade_evento": "",
        "estado_evento": "",
        "pais_evento": "",
        "link": "",
        "valor": "0",
        "detalhamento": "",
        "apresentacao": "Pôster",
        "nascimento": "99/99/9999",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cep": "123",
        "cidade": "",
        "estado": "",
        "cpf": "123.456.789-00",
        "rg": "",
        "banco": "",
        "agencia": "12a",
        "conta": "",
    }
    resp = app_post("/api/alunos", payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    esperado = {
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    }
    assert esperado.issubset(set(data["erros"])), data["erros"]
    assert "oficio" not in data or not data["oficio"]


def test_post_cpf_formato_certo_digitos_errados():
    payload = _payload_alunos_valido()
    payload["cpf"] = "111.444.777-35"
    resp = app_post("/api/alunos", payload)
    data = resp.json()
    assert data["ok"] is False
    assert "CPF inválido" in data["erros"]
    payload["cpf"] = "123.456.789-09"
    resp = app_post("/api/alunos", payload)
    assert resp.json()["ok"] is True


def test_post_data_inexistente():
    payload = _payload_alunos_valido()
    payload["nascimento"] = "31/02/1990"
    resp = app_post("/api/alunos", payload)
    data = resp.json()
    assert data["ok"] is False
    assert "Data de nascimento inválida" in data["erros"]
    payload["nascimento"] = "01/13/1990"
    resp = app_post("/api/alunos", payload)
    data = resp.json()
    assert "Data de nascimento inválida" in data["erros"]
    payload["nascimento"] = "29/02/2001"
    resp = app_post("/api/alunos", payload)
    assert "Data de nascimento inválida" in resp.json()["erros"]
    payload["nascimento"] = "29/02/2024"
    resp = app_post("/api/alunos", payload)
    assert resp.json()["ok"] is True


def _payload_alunos_valido():
    return {
        "nome_completo": "Maria da Silva Souza",
        "n_usp": "12345678",
        "programa": "Matemática Aplicada",
        "nivel": "Doutorado",
        "tipo_auxilio": "Banca de exame ou defesa",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Brasileiro de Matemática",
        "periodo": "10/03/2025 a 14/03/2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "São Paulo",
        "pais_evento": "Brasil",
        "link": "",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição",
        "apresentacao": "Pôster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "São Paulo",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }


def test_sem_acesso_externo_no_html():
    q = _html()
    for u in re.findall(r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", q):
        assert not u.startswith("http://") and not u.startswith("https://"), f"referência externa proibida: {u}"


def test_assets_servidos():
    r = app_get("/assets/usp-logo.png")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


# helpers de acesso HTTP


def app_get(caminho):
    r = _client().get(caminho)
    return r


def app_post(caminho, payload):
    return _client().post(caminho, json=payload)


def _client():
    global _CLIENTE
    try:
        return _CLIENTE
    except NameError:
        import importlib

        mod = importlib.import_module("app")
        from fastapi.testclient import TestClient

        _CLIENTE = TestClient(mod.app)
        return _CLIENTE
    finally:
        pass
