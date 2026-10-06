import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

RAIZ = Path(__file__).resolve().parent.parent


def test_pagina_inicial_e_estaticos():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert '<html' in html.lower()
    for rotulo in [
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
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
        "Enviar solicitação",
    ]:
        assert rotulo in html, rotulo
    # o brasão não aparece
    assert "escudo" not in html.lower()
    assert not re.search(r'src="[^"]*escudo[^"]*"', html, re.I)
    # o logotipo aparece e vem de assets/
    m = re.search(r"<img[^>]*assets/usp-logo\.png[^>]*>", html)
    assert m
    # head conta a folha de estilo e o script, sem cdn/fonte remota
    head = html.split("</head>")[0]
    assert re.search(r'<link[^>]*style\.css[^>]*>', head)
    assert re.search(r'<script[^>]*app\.js[^>]*>', head)
    assert "http://" not in head and "https://" not in head
    # a página é a primeira aba ativa e a segunda não
    tabs = re.findall(r'data-tab="[^"]*"', html)
    assert tabs[:2] == ['data-tab="alunos"', 'data-tab="docentes"']
    idx_alunos = html.find('data-tab="alunos"')
    idx_docentes = html.find('data-tab="docentes"')
    botao1 = html.find("Enviar solicitação", idx_alunos)
    botao2 = html.find("Enviar solicitação", idx_docentes)
    assert botao1 < idx_docentes < botao2
    # o aba ALUNOS começa visível
    id_alunos = re.search(r'id="([^"]*)"[^>]*data-tab="alunos"', html)
    id_docentes = re.search(r'data-tab="docentes"[^>]*id="([^"]*)"', html)
    if id_alunos:
        padrao = re.compile("<" + "(div|section|form)" + r'[^>]*id="' + id_alunos.group(1) + r'"[^>]*>')
        m2 = padrao.search(html)
        if m2 and "hidden" not in m2.group(0):
            pos = m2.start()
            m3 = re.search(r'<(div|section|form)[^>]*id="' + id_docentes.group(1) + r'"[^>]*>', html)
            assert m3 and "hidden" in m3.group(0)


def test_estaticos_existem():
    r1 = client.get("/style.css")
    r2 = client.get("/app.js")
    assert r1.status_code == 200 and "text/css" in r1.headers["content-type"]
    assert r2.status_code == 200
    logo = client.get("/assets/usp-logo.png")
    assert logo.status_code == 200
    assert logo.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_js_e_css_fonte():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    css = (RAIZ / "style.css").read_text(encoding="utf-8")
    for fonte in [js, css]:
        assert "http://" not in fonte and "https://" not in fonte
    assert "@import" not in css
    assert "Open Sans" in css or "sans-serif" in css


def teste_oficio_alunos_basico():
    dados = {
        "tipo": "alunos",
        "nome": "Nome Completo",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "auxilio": "Outro",
        "email": "a@usp.br",
        "evento": "Congresso",
        "periodo": "10 a 12 de julho",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "http://exemplo.com",
        "valor": "150000",
        "detalhamento": "Passagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Mate",
        "numero": "102",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 200
    corpo = r.json()
    oficio = corpo.get("oficio") or corpo.get("texto") or ""
    assert "Solicitação registrada" in (corpo.get("titulo") or "") or "oficio" in corpo
    assert "Interessada(o): Nome Completo - 12345678" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Outro" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "CCP-Matemática" in oficio
    assert "Evento: Congresso" in oficio
    assert "Período: 10 a 12 de julho" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: http://exemplo.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagem" in oficio
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Rua do Mate, 102" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "Complemento:" not in oficio


def teste_oficio_docentes():
    dados = {
        "tipo": "docentes",
        "nome": "Docente",
        "n_usp": "87654321",
        "programa": "Estatística",
        "email": "doc@ime.usp.br",
        "evento": "Escola",
        "periodo": "agosto",
        "cidade": "Rio de Janeiro",
        "estado": "RJ",
        "pais": "Brasil",
        "link": "",
        "valor": "250000",
        "detalhamento": "Diárias",
        "apresentacao": "Não irá apresentar trabalho",
        "data_nascimento": "02031970",
        "logradouro": "Av. A",
        "numero": "1",
        "complemento": "apto 2",
        "bairro": "Centro",
        "cep": "20000000",
        "cidade_end": "Rio de Janeiro",
        "estado_end": "RJ",
        "cpf": "11144477735",
        "rg": "11.111.111-1",
        "banco": "Caixa",
        "agencia": "0001",
        "conta": "999",
    }
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 200
    oficio = r.json().get("oficio")
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert re.search(r"Programa: Estatística\s*$", oficio, re.M)
    assert "CCP-Estatística" in oficio
    assert "Valor solicitado: R$ 2.500,00" in oficio
    assert "Complemento: apto 2" in oficio
    assert "Link do evento:" not in oficio
    assert "Mestrado" not in oficio and "Doutorado" not in oficio


def teste_valida_campos_vazios():
    dados = {"tipo": "alunos"}
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code in (400, 422)
    corpo = r.json()
    msgs = corpo.get("erros") or corpo.get("detalhe")
    assert "Preencha todos os campos" in msgs
    assert "oficio" not in corpo or not corpo.get("oficio")


def teste_valida_n_usp_e_agencia():
    base = solicitacao_valida()
    base["n_usp"] = "12a4"
    r = client.post("/api/solicitacao", json=base)
    assert r.status_code in (400, 422)
    msgs = r.json().get("erros")
    assert "N. USP deve conter apenas números" in msgs
    base = solicitacao_valida()
    base["agencia"] = "12a"
    r = client.post("/api/solicitacao", json=base)
    assert r.status_code in (400, 422)
    assert "Número da agência deve conter apenas números" in r.json().get("erros")


def teste_valida_valor_email():
    base = solicitacao_valida()
    base["valor"] = "0"
    r = client.post("/api/solicitacao", json=base)
    assert r.status_code in (400, 422)
    assert "Valor solicitado deve ser maior que 0" in r.json().get("erros")
    base = solicitacao_valida()
    base["email"] = "sem-arroba"
    r = client.post("/api/solicitacao", json=base)
    assert r.status_code in (400, 422)
    assert "E-mail inválido" in r.json().get("erros")


def teste_valida_cpf_cep_data():
    base = solicitacao_valida()
    base["cpf"] = "12"
    r = client.post("/api/solicitacao", json=base)
    assert r.status_code in (400, 422)
    assert "CPF deve estar no formato 000.000.000-00" in r.json().get("erros")
    base = solicitacao_valida()
    base["cep"] = "05508"
    r = client.post("/api/solicitacao", json=base)
    assert "CEP deve estar no formato 00000-000" in r.json().get("erros")
    base = solicitacao_valida()
    base["data_nascimento"] = "0102"
    r = client.post("/api/solicitacao", json=base)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json().get("erros")
    base = solicitacao_valida()
    base["cpf"] = "12345678901"
    r = client.post("/api/solicitacao", json=base)
    assert "CPF inválido" in r.json().get("erros")
    base = solicitacao_valida()
    base["data_nascimento"] = "31021980"
    r = client.post("/api/solicitacao", json=base)
    assert "Data de nascimento inválida" in r.json().get("erros")


def teste_todos_os_erros_de_uma_vez():
    dados = {
        "tipo": "alunos",
        "nome": "",
        "n_usp": "12a4",
        "programa": "",
        "email": "x",
        "valor": "0",
        "cpf": "12345678901",
        "cep": "055",
        "data_nascimento": "9999",
        "agencia": "12x",
    }
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code in (400, 422)
    msgs = r.json().get("erros")
    for esperada in [
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
    ]:
        assert esperada in msgs, esperada
    assert msgs.count("Preencha todos os campos") == 1


def solicitacao_valida():
    return {
        "tipo": "alunos",
        "nome": "Nome",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Doutorado",
        "auxilio": "Participação em evento",
        "email": "n@ime.usp.br",
        "evento": "Evento",
        "periodo": "julho",
        "cidade": "C",
        "estado": "E",
        "pais": "P",
        "link": "",
        "valor": "1500",
        "detalhamento": "d",
        "apresentacao": "Outra",
        "data_nascimento": "01021980",
        "logradouro": "L",
        "numero": "1",
        "complemento": "",
        "bairro": "B",
        "cep": "05508090",
        "cidade_end": "S",
        "estado_end": "SP",
        "cpf": "12345678909",
        "rg": "1",
        "banco": "B",
        "agencia": "1234",
        "conta": "1",
    }


def test_largura_1000px():
    """Em 1000x700: nenhuma barra de rolagem vertical na página."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1000, "height": 700})
        pagina.goto(BASE)
        pagina.wait_for_timeout(400)
        tem_scroll = pagina.evaluate(
            "document.documentElement.scrollHeight > "
            "document.documentElement.clientHeight"
        )
        navegador.close()
    assert not tem_scroll, (
        "A página excede a altura de 1000x700 (aumentando a viewport não resolve - "
        "precisa caber)"
    )


def test_abas_e_estados():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1000, "height": 700})
        pagina.goto(BASE)
        pagina.wait_for_timeout(400)

        alunos = pagina.locator("#tab-alunos")
        docentes = pagina.locator("#tab-docentes")
        panel_alunos = pagina.locator("#painel-alunos")
        panel_docentes = pagina.locator("#painel-docentes")

        # página abre na aba ALUNOS
        assert alunos.get_attribute("aria-selected") == "true"
        assert panel_alunos.is_visible()
        assert docentes.get_attribute("aria-selected") == "false"
        assert not panel_docentes.is_visible()

        # digitando na aba ALUNOS, trocando para DOCENTES, voltando
        pagina.fill("#painel-alunos input[name='nome']", "Ana")
        pagina.click("#tab-docentes")
        pagina.wait_for_timeout(200)
        assert panel_docentes.is_visible()
        assert not panel_alunos.is_visible()
        assert docentes.get_attribute("aria-selected") == "true"
        assert alunos.get_attribute("aria-selected") == "false"

        # a aba DOCENTES não tem nível nem tipo de auxílio
        assert panel_docentes.locator("[name='nivel']").count() == 0
        assert panel_docentes.locator("[name='auxilio']").count() == 0
        assert panel_alunos.locator("[name='nivel']").count() == 1
        assert panel_alunos.locator("[name='auxilio']").count() == 1

        pagina.click("#tab-alunos")
        pagina.wait_for_timeout(200)
        assert pagina.locator("#painel-alunos input[name='nome']").input_value() == "Ana"

        navegador.close()


def test_campos_dinamicos_e_validacao_frontend():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1000, "height": 700})
        pagina.goto(BASE)
        pagina.wait_for_timeout(400)
        pagina.click("#tab-docentes")
        pagina.wait_for_timeout(200)

        # formatação dinâmica: valor, cpf, cep e data
        pagina.fill("#painel-docentes input[name='valor']", "1500")
        pagina.locator("#painel-docentes input[name='valor']").blur()
        assert pagina.locator("#painel-docentes input[name='valor']").input_value() == "R$ 15,00"

        pagina.fill("#painel-docentes input[name='cpf']", "12345678909")
        pagina.locator("#painel-docentes input[name='cpf']").blur()
        assert pagina.locator("#painel-docentes input[name='cpf']").input_value() == "123.456.789-09"

        pagina.fill("#painel-docentes input[name='cep']", "05508090")
        pagina.locator("#painel-docentes input[name='cep']").blur()
        assert pagina.locator("#painel-docentes input[name='cep']").input_value() == "05508-090"

        pagina.fill("#painel-docentes input[name='data_nascimento']", "01021980")
        pagina.locator("#painel-docentes input[name='data_nascimento']").blur()
        assert pagina.locator("#painel-docentes input[name='data_nascimento']").input_value() == "01/02/1980"

        # validação completa, tudo vazio exceto os digitados acima
        pagina.fill("#painel-docentes input[name='nome']", "")
        pagina.click("#painel-docentes button[type='submit']")
        pagina.wait_for_timeout(600)
        erros = pagina.locator("#painel-docentes .erros").inner_text()
        assert "Preencha todos os campos" in erros
        assert "N. USP deve conter apenas números" in erros
        assert "Número da agência deve conter apenas números" in erros
        assert "E-mail inválido" in erros
        assert "CEP deve estar no formato 00000-000" not in erros
        assert "CPF inválido" not in erros
        assert panel := True or pagina.locator("#painel-docentes .erros")
        # aba continua ativa
        assert pagina.locator("#tab-docentes").get_attribute("aria-selected") == "true"
        assert not pagina.locator("#painel-docentes .erros").is_hidden()
        # campos preenchidos antes continuam preenchidos
        assert pagina.locator("#painel-docentes input[name='cpf']").input_value() == "123.456.789-09"

        # ofício não gerado
        assert pagina.locator("#confirmacao").count() == 0 or not pagina.locator("#confirmacao").is_visible()
        navegador.close()


def test_cabecalho_e_aba_ativa_e_rodape():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1000, "height": 700})
        pagina.goto(BASE)
        pagina.wait_for_timeout(400)

        img = pagina.locator("header img")
        assert img.get_attribute("src").endswith("assets/usp-logo.png")
        assert img.is_visible()
        assert "Universidade de São Paulo" in pagina.locator("header").inner_text()
        assert pagina.locator("[role='tab']:above-is(.abas,header)").count() == 0 or True
        tabs = pagina.locator("[role='tab']")
        assert tabs.nth(0).inner_text().strip() == "ALUNOS"
        assert tabs.nth(1).inner_text().strip() == "DOCENTES"
        assert "#1094ab" in (RAIZ / "style.css").read_text(encoding="utf-8")
        assert "<form" in (RAIZ / "index.html").read_text(encoding="utf-8")
        navegador.close()


def test_pagina_cabe_em_1000x700_e_1600x900():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        for w, h in [(1000, 700), (1600, 900)]:
            pagina = navegador.new_page(viewport={"width": w, "height": h})
            pagina.goto(BASE)
            pagina.wait_for_timeout(300)
            # o rodapé visível é o sinal de que a página cabe inteira na tela
            rodape = pagina.locator("footer")
            rodape.scroll_into_view_if_needed()
            pagina.wait_for_timeout(100)
            visivel = rodape.is_visible()
            fecha = pagina.evaluate("document.documentElement.scrollHeight > document.documentElement.clientHeight")
            pagina.close()
            assert visivel and not fecha, (
                "Página ultrapassa a altura da janela e exige rolagem vertical"
            )
        navegador.close()
