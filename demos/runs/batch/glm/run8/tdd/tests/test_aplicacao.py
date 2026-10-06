import re
from fastapi.testclient import TestClient

from app import app


def client():
    return TestClient(app)


def dados_alunos(**overrides):
    dados = {
        "aba": "alunos",
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de julho de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com",
        "valor": "150000",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Teste",
        "numero": "100",
        "complemento": "",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade_endereco": "São Paulo",
        "estado_endereco": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(overrides)
    return dados


def dados_docentes(**overrides):
    dados = dados_alunos()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados["aba"] = "docentes"
    dados.update(overrides)
    return dados


def test_estaticos_disponiveis():
    c = client()
    for caminho, fragmento in [
        ("/", "<!DOCTYPE html>"),
        ("/style.css", "Open Sans"),
        ("/app.js", ""),
        ("/assets/usp-logo.png", ""),
    ]:
        r = c.get(caminho)
        assert r.status_code == 200
        assert fragmento in r.text


def test_html_abas_blocos_rotulos():
    r = client().get("/")
    html = r.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    for bloco in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert html.index(bloco) < html.index("ENDEREÇO DO SOLICITANTE")
    assert "Enviar solicitação" in html


def test_campos_alunos():
    r = client().get("/")
    html = r.text
    for rotulo in [
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
    ]:
        assert rotulo in html
    for opcao in ["Mestrado", "Doutorado", "Participação em evento", "Banca de exame ou defesa", "Outro", "Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert opcao in html


def test_docentes_sem_nivel_e_tipo():
    """A aba DOCENTES não tem NÍVEL nem TIPO DE AUXÍLIO, ALUNOS tem."""
    r = client().get("/")
    html = r.text
    # os rótulos aparecem porque pertencem ao formulário de ALUNOS
    assert "NÍVEL" in html and "TIPO DE AUXÍLIO" in html
    # cada formulário é um <form> distinto: extrai os dois e compara
    forms = re.findall(r"<form.*?</form>", html, re.S)
    assert len(forms) == 2
    if "ALUNOS" in html.split("<form")[0]:
        form_alunos, form_docentes = forms[0], forms[1]
    else:
        form_docentes, form_alunos = forms[0], forms[1]
    assert "NÍVEL" in form_alunos and "TIPO DE AUXÍLIO" in form_alunos
    assert "NÍVEL" not in form_docentes and "TIPO DE AUXÍLIO" not in form_docentes


def test_placeholders_sao_exemplos():
    r = client().get("/")
    html = r.text
    placeholders = re.findall(r'placeholder="([^"]+)"', html)
    assert placeholders  # existem
    # não podem repetir o próprio rótulo do campo
    rotulos = set(re.findall(r">([^<>{}]+)</label>", html))
    for p in placeholders:
        assert p.strip() not in rotulos


def test_css_identidade():
    css = client().get("/style.css").text.lower()
    for cor in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert cor in css
    # azul primário é o logotipo e domina a página
    assert css.count("#1094ab") > css.count("#64c4d2")
    assert css.count("#1094ab") > css.count("#fcb421")
    assert "sans-serif" in css


def test_js_formatacao():
    js = client().get("/app.js").text
    assert "1500" in js or "15,00" in js
    assert "12345678909" in js or "123.456.789-09" in js


def test_oficio_alunos():
    c = client()
    r = c.post("/solicitar", json=dados_alunos())
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["valido"] is True
    oficio = corpo["oficio"]
    assert corpo.get("aba", "alunos") == "alunos"
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a" in oficio
    assert "interessada(o) acima, conforme segue:" in oficio
    assert "Evento: Congresso Nacional de Matemática" in oficio
    assert "Período: 10 a 12 de julho de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Inscrição e hospedagem" in oficio
    assert "Rua do Teste, 100" in oficio
    assert "Complemento:" not in oficio
    assert "CEP: 05508-090" in oficio
    assert "Centro, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_docentes():
    c = client()
    r = c.post("/solicitar", json=dados_docentes())
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["valido"] is True
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert " - Mestrado" not in oficio


def test_oficio_linhas_opcionais():
    c = client()
    corpo = c.post("/solicitar", json=dados_alunos(link="", complemento="Apto 12")).json()
    oficio = corpo["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento: Apto 12" in oficio


def test_campos_obrigatorios_vazios():
    c = client()
    dados = dados_alunos()
    for campo in ["nome", "n_usp", "programa", "email", "evento", "periodo", "cidade", "estado", "pais", "valor", "detalhamento", "logradouro", "numero", "bairro", "cep", "cidade_endereco", "estado_endereco", "cpf", "rg", "banco", "agencia", "conta", "nascimento", "nivel", "tipo_auxilio", "apresentacao"]:
        dados = dados_alunos(**{campo: ""})
        corpo = c.post("/solicitar", json=dados).json()
        assert corpo["valido"] is False
        assert "Preencha todos os campos" in corpo["erros"]
        assert "oficio" not in corpo or corpo.get("oficio") is None


def test_opcionais_podem_ficar_vazios():
    c = client()
    corpo = c.post("/solicitar", json=dados_alunos(link="", complemento="")).json()
    assert corpo["valido"] is True


def test_erro_n_usp():
    corpo = client().post("/solicitar", json=dados_alunos(n_usp="12.345-6")).json()
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_erro_agencia():
    corpo = client().post("/solicitar", json=dados_alunos(agencia="12a4")).json()
    assert "Número da agência deve conter apenas números" in corpo["erros"]


def test_erro_valor_zero_e_negativo():
    for valor in ["0", "-5"]:
        corpo = client().post("/solicitar", json=dados_alunos(valor=valor)).json()
        assert corpo["valido"] is False
        assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_erro_valor_nao_natural():
    for valor in ["12,50", "abc", "1.5"]:
        corpo = client().post("/solicitar", json=dados_alunos(valor=valor)).json()
        assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_erro_email():
    for email in ["sem-arroba", "maria@", "@ime.usp.br", "maria@ime"]:
        corpo = client().post("/solicitar", json=dados_alunos(email=email)).json()
        assert "E-mail inválido" in corpo["erros"]


def test_erro_cpf_formato():
    for cpf in ["12345678909", "12.345.678-909", "abc.def.ghi-jk"]:
        corpo = client().post("/solicitar", json=dados_alunos(cpf=cpf)).json()
        assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]


def test_erro_cpf_verificador():
    corpo = client().post("/solicitar", json=dados_alunos(cpf="123.456.789-00")).json()
    assert "CPF inválido" in corpo["erros"]
    assert "CPF deve estar no formato 000.000.000-00" not in corpo["erros"]


def test_erro_cep():
    for cep in ["05508-0900", "05508090", "05508-09", "abcdefgh"]:
        corpo = client().post("/solicitar", json=dados_alunos(cep=cep)).json()
        assert "CEP deve estar no formato 00000-000" in corpo["erros"]


def test_erro_data_formato():
    for nascimento in ["01021980", "1/2/1980", "01-02-1980", "01/02/980", "010219800"]:
        corpo = client().post("/solicitar", json=dados_alunos(nascimento=nascimento)).json()
        assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]


def test_erro_data_inexistente():
    for nascimento in ["31/02/1980", "01/13/1980", "32/01/1980", "00/01/1980", "01/00/1980"]:
        corpo = client().post("/solicitar", json=dados_alunos(nascimento=nascimento)).json()
        assert "Data de nascimento inválida" in corpo["erros"]


def test_todos_erros_juntos():
    dados = dados_alunos(
        nome="",
        n_usp="abc",
        agencia="x1",
        valor="0",
        email="errado",
        cpf="111",
        cep="111",
        nascimento="31/02/1980",
    )
    corpo = client().post("/solicitar", json=dados).json()
    erros = corpo["erros"]
    for msg in [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento inválida",
    ]:
        assert msg in erros
    assert corpo["valido"] is False
    assert corpo.get("oficio") is None


def test_aba_preservada_no_erro():
    corpo = client().post("/solicitar", json=dados_docentes(nome="")).json()
    assert corpo["valido"] is False
    assert corpo.get("aba") == "docentes"


def test_valores_devolvidos_para_nao_perder_digitacao():
    dados = dados_docentes(nome="")
    corpo = client().post("/solicitar", json=dados).json()
    assert "Preencha todos os campos" in corpo["erros"]
    assert corpo["valido"] is False
    # o frontend precisa manter o que foi digitado; a resposta devolve os dados
    assert corpo.get("dados", {}).get("programa") == "Matemática"


def test_valores_formatados_do_valor():
    for digitado, esperado in [
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
    ]:
        corpo = client().post("/solicitar", json=dados_alunos(valor=digitado)).json()
        assert corpo["valido"] is True
        assert f"Valor solicitado: {esperado}" in corpo["oficio"]


def test_formato_valor_no_backend():
    """O backend devolve o valor formatado em moeda brasileira."""
    corpo = client().post("/solicitar", json=dados_alunos(valor="150000")).json()
    assert "R$ 1.500,00" in str(corpo.get("dados", {}).get("valor", "")) or "R$ 1.500,00" in corpo["oficio"]


def test_formato_sem_nivel_em_erro_docentes():
    """DOCENTES com valor inválido: erro aparece igual, sem exigir NÍVEL."""
    corpo = client().post("/solicitar", json=dados_docentes(valor="0")).json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]
    assert "Preencha todos os campos" not in corpo["erros"]


def test_persistencia_nao_existe():
    """Sem banco/arquivo: resposta deve ser rápida e endpoint não grava nada."""
    c = client()
    r = c.post("/solicitar", json=dados_alunos())
    assert r.status_code == 200
    import os
    # nenhum arquivo de dados deve ser criado na raiz além dos estáticos
    for nome in os.listdir("."):
        assert not nome.endswith(".db")
        assert nome != "solicitacoes.json"


def test_js_sem_framework_sem_cdn():
    for arquivo in ["/", "/style.css", "/app.js"]:
        conteudo = client().get(arquivo).text
        assert "http://" not in conteudo or "127.0.0.1" in conteudo
        assert "https://" not in conteudo
        for lib in ["vue", "react", "angular", "jquery", "bootstrap"]:
            assert lib not in conteudo.lower()


def test_confirmacao_rotulos_frontend():
    """A página traz o título e a estrutura de confirmação."""
    html = client().get("/").text
    assert "Solicitação registrada" in html or "Solicitação registrada" in client().get("/app.js").text


def test_cabecalho_identidade():
    html = client().get("/").text
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    # o brasão/escudo não aparece na página
    assert not re.search(r"escudo|brasao|brasão", html, re.I) or not re.search(r'<img[^>]*(escudo|brasao|brasão)[^>]*>', html, re.I)


def test_tela_unica_sem_rolagem_vertical():
    """Layout em colunas: CSS usa grid ou flex para distribuir horizontalmente."""
    css = client().get("/style.css").text.lower()
    assert "grid" in css or "flex" in css
    assert "overflow" not in css or "overflow-y" not in css


def test_agencia_e_n_usp_digitos_validos():
    c = client()
    for dados in [dados_alunos(), dados_docentes()]:
        corpo = c.post("/solicitar", json=dados).json()
        assert corpo["valido"] is True
        assert corpo["erros"] == []
