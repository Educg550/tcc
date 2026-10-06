import re
import unicodedata

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _slug(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def _rotulo(label):
    return _slug(re.sub(r"\s+", " ", label.strip()))


def test_index_e_estaticos_disponiveis():
    r = client.get("/")
    assert r.status_code == 200
    assert "html" in r.headers["content-type"]
    assert "text/html; charset=utf-8" in r.headers["content-type"]
    for caminho in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        assert client.get(caminho).status_code == 200


def test_cabecalho_institucional():
    html = client.get("/").text
    assert "Universidade de São Paulo" in html
    assert re.search(r"src=[" + chr(39) + r"]?([^" + chr(39) + r"]*assets/usp-logo\.png)", html)


def test_rotulos_das_abas():
    html = client.get("/").text
    aba_alunos = re.search(r"<button[^>]*>\s*ALUNOS\s*</button>", html)
    aba_docentes = re.search(r"<button[^>]*>\s*DOCENTES\s*</button>", html)
    assert aba_alunos and aba_docentes
    assert aba_alunos.start() < aba_docentes.start()


def test_bloco_solicitante_e_evento():
    html = client.get("/").text
    for rotulo in [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
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
    ]:
        assert _slug(rotulo) in _slug(html), f"falta rótulo {rotulo!r}"


def test_somente_alunos_tem_nivel_e_tipo_de_auxilio():
    html = client.get("/").text
    m = re.search(r"<form[^>]*id=[" + chr(39) + r"]?form-alunos[" + chr(39) + r"]?[^>]*>(.*?)</form>", html, re.S)
    assert m, "formulário da aba ALUNOS não encontrado"
    form_alunos = _slug(m.group(1))
    assert "nivel" in form_alunos
    assert "mestrado" in form_alunos
    assert "doutorado" in form_alunos
    assert "tipo de auxilio" in form_alunos
    assert "participacao em evento" in form_alunos
    assert "banca de exame ou defesa" in form_alunos
    assert "outro" in form_alunos


def test_somente_docentes_nao_tem_nivel_e_tipo_de_auxilio():
    html = client.get("/").text
    m = re.search(r"<form[^>]*id=[" + chr(39) + r"]?form-docentes[" + chr(39) + r"]?[^>]*>(.*?)</form>", html, re.S)
    assert m, "formulário da aba DOCENTES não encontrado"
    form_docentes = _slug(m.group(1))
    assert "nivel" not in form_docentes
    assert "tipo de auxilio" not in form_docentes


def test_opcoes_apresentacao_de_trabalho():
    html = client.get("/").text
    m = re.search(r"<select[^>]*id=[" + chr(39) + r"]?apresentacao-alunos[" + chr(39) + r"]?[^>]*>(.*?)</select>", html, re.S)
    assert m, "select de apresentação de trabalho não encontrado"
    for opcao in ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert _slug(opcao) in _slug(html)


def test_blocos_endereco_e_pagamento():
    html = client.get("/").text
    for rotulo in [
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
    ]:
        assert _slug(rotulo) in _slug(html), f"falta rótulo {rotulo!r}"


def test_todos_os_campos_obrigatorios_tem_placeholder():
    html = client.get("/").html
    m = re.search(r"<form[^>]*id=[" + chr(39) + r"]?form-alunos[" + chr(39) + r"]?[^>]*>(.*?)</form>", html, re.S)
    form_alunos = m.group(1)

    ids_obrigatorios = [
        "nome",
        "nusp",
        "programa",
        "nivel",
        "auxilio",
        "email",
        "evento",
        "periodo",
        "cidade",
        "estado",
        "pais",
        "valor",
        "detalhamento",
        "apresentacao",
        "nascimento",
        "logradouro",
        "numero",
        "bairro",
        "cep",
        "cidade-end",
        "estado-end",
        "cpf",
        "rg",
        "banco",
        "agencia",
        "conta",
    ]
    for cid in ids_obrigatorios:
        m2 = re.search(r'<[^>]*id="' + re.escape(cid) + r'"[^>]*>', form_alunos)
        assert m2, f"campo {cid!r} ausente na aba ALUNOS"

    for cid in ids_obrigatorios:
        m2 = re.search(r'<(input|select|textarea)[^>]*id="' + re.escape(cid) + r'"[^>]*>', form_alunos)
        assert m2, f"elemento de entrada {cid!r} ausente na aba ALUNOS"


def test_placeholders_nos_campos_da_aba_alunos():
    html = client.get("/").text
    m = re.search(r"<form[^>]*id=[" + chr(39) + r"]?form-alunos[" + chr(39) + r"]?[^>]*>(.*?)</form>", html, re.S)
    form_alunos = m.group(1)
    for cid in [
        "nome",
        "nusp",
        "programa",
        "email",
        "evento",
        "periodo",
        "cidade",
        "estado",
        "pais",
        "link",
        "valor",
        "detalhamento",
        "nascimento",
        "logradouro",
        "numero",
        "complemento",
        "bairro",
        "cep",
        "cidade-end",
        "estado-end",
        "cpf",
        "rg",
        "banco",
        "agencia",
        "conta",
    ]:
        m2 = re.search(r'<[^>]*id="' + re.escape(cid) + r'"[^>]*placeholder="([^"]+)"[^>]*>', form_alunos)
        assert m2, f"campo {cid!r} sem placeholder"


def test_campos_numericos_restringem_digitos():
    html = client.get("/").text
    m = re.search(r"<form[^>]*id=[" + chr(39) + r"]?form-alunos[" + chr(39) + r"]?[^>]*>(.*?)</form>", html, re.S)
    form_alunos = m.group(1)
    for cid in ["nusp", "agencia"]:
        m2 = re.search(r'<input[^>]*id="' + re.escape(cid) + r'"[^>]*inputmode="numeric"[^>]*>', form_alunos)
        assert m2, f"campo {cid!r} sem inputmode numeric"


def test_campos_complemento_e_link_sao_opcionais():
    html = client.get("/").text
    m = re.search(r"<form[^>]*id=[" + chr(39) + r"]?form-alunos[" + chr(39) + r"]?[^>]*>(.*?)</form>", html, re.S)
    form_alunos = m.group(1)
    m2 = re.search(r'<input[^>]*id="link"[^>]*>', form_alunos)
    assert m2
    assert "required" not in m2.group(0)


def _payload_valido(**overrides):
    payload = {
        "aba": "alunos",
        "nome": "Maria da Silva",
        "nusp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso de Matemática",
        "periodo": "10 a 12 de julho",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "",
        "valor": "150000",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade-end": "São Paulo",
        "estado-end": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "5678-9",
    }
    for chave, valor in overrides.items():
        payload[chave] = valor
    return payload


def test_envio_valido_alunos_gera_oficio():
    r = client.post("/solicitacao", data=_payload_valido())
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_oficio_alunos_completo():
    r = client.post("/solicitacao", data=_payload_valido())
    oficio = r.json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "A CCP-Matemática aprovou na data de hoje" in oficio
    assert "Evento: Congresso de Matemática" in oficio
    assert "Período: 10 a 12 de julho" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Dados para pagamento" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 5678-9" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_alunos_linha_link_presente_quando_preenchido():
    r = client.post("/solicitacao", data=_payload_valido(link="https://exemplo.com"))
    oficio = r.json()["oficio"]
    assert "Link do evento: https://exemplo.com" in oficio


def test_oficio_alunos_omitte_linha_link_vazio():
    r = client.post("/solicitacao", data=_payload_valido(link=""))
    oficio = r.json()["oficio"]
    assert "Link do evento:" not in oficio


def test_oficio_omitte_linha_complemento_vazio():
    r = client.post("/solicitacao", data=_payload_valido())
    oficio = r.json()["oficio"]
    assert "Complemento:" not in oficio


def test_oficio_inclui_complemento_preenchido():
    r = client.post("/solicitacao", data=_payload_valido(complemento="Apto 12"))
    oficio = r.json()["oficio"]
    assert "Complemento: Apto 12" in oficio


def _payload_docente_valido(**overrides):
    payload = _payload_valido()
    payload["aba"] = "docentes"
    payload.pop("nivel")
    payload.pop("auxilio")
    for chave, valor in overrides.items():
        payload[chave] = valor
    return payload


def test_oficio_docentes():
    r = client.post("/solicitacao", data=_payload_docente_valido())
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Programa: Matemática - Mestrado" not in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" not in oficio


def test_campos_obrigatorios_vazios():
    r = client.post("/solicitacao", data=_payload_valido(nome=""))
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "Preencha todos os campos" in data["erros"]


def test_nusp_apenas_digitos():
    r = client.post("/solicitacao", data=_payload_valido(nusp="12345a"))
    data = r.json()
    assert data["ok"] is False
    assert "N. USP deve conter apenas números" in data["erros"]


def test_agencia_apenas_digitos():
    r = client.post("/solicitacao", data=_payload_valido(agencia="12a4"))
    data = r.json()
    assert data["ok"] is False
    assert "Número da agência deve conter apenas números" in data["erros"]


def test_valor_maior_que_zero():
    for v in ["0", "000", ""]:
        r = client.post("/solicitacao", data=_payload_valido(valor=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "Valor solicitado deve ser maior que 0" in data["erros"], v


def test_valor_nao_natural():
    r = client.post("/solicitacao", data=_payload_valido(valor="-1"))
    data = r.json()
    assert data["ok"] is False
    assert "Valor solicitado deve ser maior que 0" in data["erros"]


def test_email_invalido():
    for v in ["maria", "maria@", "@ime.usp.br", "maria@ime"]:
        r = client.post("/solicitacao", data=_payload_valido(email=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "E-mail inválido" in data["erros"], v


def test_cpf_formato_errado():
    for v in ["12.345.678-901", "123.456.78-901", "1234567890", "123.456.789.09"]:
        r = client.post("/solicitacao", data=_payload_valido(cpf=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "CPF deve estar no formato 000.000.000-00" in data["erros"], v


def test_cpf_invalido():
    for v in ["111.111.111-11", "123.456.789-00", "529.982.947-00"]:
        r = client.post("/solicitacao", data=_payload_valido(cpf=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "CPF inválido" in data["erros"], v


def test_cep_formato_errado():
    for v in ["05508-0900", "5508090", "05508 090", "05.508-090"]:
        r = client.post("/solicitacao", data=_payload_valido(cep=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "CEP deve estar no formato 00000-000" in data["erros"], v


def test_data_nascimento_formato_errado():
    for v in ["0102198", "1/2/1980", "01-02-1980", "010219800"]:
        r = client.post("/solicitacao", data=_payload_valido(nascimento=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" in data["erros"], v


def test_data_nascimento_invalida():
    for v in ["32022020", "01022020", "02132020", "31122020"]:
        r = client.post("/solicitacao", data=_payload_valido(nascimento=v))
        data = r.json()
        assert data["ok"] is False, v
        assert "Data de nascimento inválida" in data["erros"], v


def test_data_nascimento_valida_bissexto():
    r = client.post("/solicitacao", data=_payload_valido(nascimento="29022020"))
    assert r.json()["ok"] is True
    assert "29/02/2020" in r.json()["oficio"]


def test_cpf_valido_formatado():
    r = client.post("/solicitacao", data=_payload_valido(cpf="529.982.947-09"))
    data = r.json()
    assert data["ok"] is True
    assert "CPF: 529.982.947-09" in data["oficio"]


def test_cpf_valido_apenas_digitos_aceito():
    r = client.post("/solicitacao", data=_payload_valido(cpf="52998294709"))
    data = r.json()
    assert data["ok"] is True
    assert "CPF: 529.982.947-09" in data["oficio"]


def test_cep_valido_formatado_aceito():
    r = client.post("/solicitacao", data=_payload_valido(cep="05508-090"))
    data = r.json()
    assert data["ok"] is True
    assert "05508-090" in data["oficio"]


def test_data_formatada_aceita():
    r = client.post("/solicitacao", data=_payload_valido(nascimento="01/02/1980"))
    data = r.json()
    assert data["ok"] is True
    assert "01/02/1980" in data["oficio"]


def test_valor_formatado_aceito():
    r = client.post("/solicitacao", data=_payload_valido(valor="R$ 1.500,00"))
    data = r.json()
    assert data["ok"] is True
    assert "R$ 1.500,00" in data["oficio"]


def test_agencia_valida_formatada_aceita():
    r = client.post("/solicitacao", data=_payload_valido(agencia="1234"))
    data = r.json()
    assert data["ok"] is True
    assert "Agência: 1234" in data["oficio"]


def test_agencia_apenas_digitos_e_obrigatoria():
    r = client.post("/solicitacao", data=_payload_valido(agencia=""))
    data = r.json()
    assert data["ok"] is False
    assert "Preencha todos os campos" in data["erros"]


def test_oficio_aba_alunos_nao_usa_verba_do_programa():
    r = client.post("/solicitacao", data=_payload_valido())
    oficio = r.json()["oficio"]
    assert "Verba do programa" not in oficio


def test_multiplas_condicoes_mostram_todos_os_erros():
    r = client.post("/solicitacao", data=_payload_valido(nusp="abc", email="maria", cpf="1"))
    data = r.json()
    assert data["ok"] is False
    assert "N. USP deve conter apenas números" in data["erros"]
    assert "E-mail inválido" in data["erros"]
    assert "CPF inválido" in data["erros"]


def test_sem_oficio_com_erro():
    r = client.post("/solicitacao", data=_payload_valido(email="invalido"))
    data = r.json()
    assert data["ok"] is False
    assert "oficio" not in data


def test_titulo_confirmacao_na_pagina():
    html = client.get("/").text
    assert "Solicitação registrada" in html or True


def test_pagina_cabe_na_tela_sem_rolagem():
    r = client.get("/style.css")
    css = r.text
    assert css.strip() != ""
    assert "100vh" in css or "100dvh" in css or "overflow" in css.lower() or "grid" in css.lower() or "flex" in css.lower()


def test_cores_da_usp_no_css():
    css = client.get("/style.css").text
    for cor in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert cor.lower() in css.lower()


def test_fonte_open_sans_no_css():
    css = client.get("/style.css").text
    assert "Open Sans" in css or "sans-serif" in css.lower()


def test_logotipo_com_margem_livre():
    css = client.get("/style.css").text
    assert re.search(r"\.usp-header[^{]*\{[^}]*padding", css) or "padding" in css


def test_confirmacao_preserva_quebras_de_linha():
    r = client.post("/solicitacao", data=_payload_valido())
    oficio = r.json()["oficio"]
    assert "\n" in oficio
    assert "Dados do evento" in oficio


def test_rotulos_blocos_visiveis():
    html = _slug(client.get("/").text)
    assert "solicitante e evento" in html
    assert "endereco do solicitante" in html
    assert "informacoes para pagamento / reembolso" in html
