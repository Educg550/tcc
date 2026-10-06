import re
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

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

ROTULOS_DOCENTES = [r for r in ROTULOS_ALUNOS if r not in ("NÍVEL", "TIPO DE AUXÍLIO")]


def _html_da_home():
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.text


def _texto_sem_tags(html):
    texto = re.sub(r"<[^>]+>", "\n", html)
    return "\n".join(linha.strip() for linha in texto.splitlines() if linha.strip())


def test_home_serve_html_com_abas_alunos_e_docentes():
    html = _html_da_home()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_aba_alunos_ativa_por_padrao():
    html = _html_da_home()
    m = re.search(r"<[^>]*id=[\"']alunos[\"'][^>]*>", html, re.IGNORECASE)
    if m:
        assert "active" in m.group(0).lower() or "active" in m.group(0)
    else:
        m = re.search(r"(class=[\"'][^\"']*active[^\"']*[\"'][^>]*>[^<]*ALUNOS)", html)
        assert m is not None


def test_rotulos_da_aba_alunos():
    texto = _texto_sem_tags(_html_da_home())
    for rotulo in ROTULOS_ALUNOS:
        assert rotulo in texto, f"Rótulo ausente: {rotulo}"


def test_rotulos_da_aba_docentes():
    texto = _texto_sem_tags(_html_da_home())
    for rotulo in ROTULOS_DOCENTES:
        assert rotulo in texto, f"Rótulo ausente na aba docentes: {rotulo}"


def test_blocos_titulos_visiveis():
    texto = _texto_sem_tags(_html_da_home())
    for bloco in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert bloco in texto


def test_botao_enviar_solicitacao_presente_em_cada_aba():
    html = _html_da_home()
    assert html.count("Enviar solicitação") >= 2


def test_todos_os_campos_tem_placeholder_visivel():
    html = _html_da_home()
    placeholders = re.findall(r'placeholder=["\']([^"\']*)["\']', html)
    assert placeholders
    for valor in placeholders:
        assert valor.strip()


def test_cabecalho_institucional():
    html = _html_da_home()
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    assert "brasão" not in html.lower()
    assert "escudo" not in html.lower()


def test_cores_institucionais_no_css():
    resp = client.get("/style.css")
    assert resp.status_code == 200
    css = resp.text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_open_sans_ou_sem_serifa_no_css():
    css = client.get("/style.css").text.lower()
    assert "sans-serif" in css


def test_js_carrega_formatos_no_blur():
    resp = client.get("/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "blur" in js


def _payload_valido_alunos(**overrides):
    dados = {
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Simpósio Internacional",
        "periodo": "10 a 15 de janeiro de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.example.com",
        "valor_solicitado": "1.500,00",
        "detalhamento": "Passagens e hospedagem",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Cidade Universitária",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "111.444.777-35",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
        "aba": "alunos",
    }
    dados.update(overrides)
    return dados


def _payload_docente(**overrides):
    dados = _payload_valido_alunos(**overrides)
    dados["aba"] = "docentes"
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    return dados


def _oficio(resp):
    if hasattr(resp, "json"):
        try:
            return resp.json().get("oficio", "")
        except Exception:
            pass
    texto = getattr(resp, "text", "")
    return texto


def test_envio_valido_gera_oficio_alunos_com_dados():
    resp = client.post("/solicitar", json=_payload_valido_alunos())
    assert resp.status_code == 200
    oficio = _oficio(resp)
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "Evento: Simpósio Internacional" in oficio
    assert "Período: 10 a 15 de janeiro de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://evento.example.com" in oficio
    assert "Apresentação de trabalho: Apresentação oral" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Passagens e hospedagem" in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco B" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Cidade Universitária, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 111.444.777-35" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio


def test_oficio_docentes_sem_nivel_e_tipo_de_auxilio():
    resp = client.post("/solicitar", json=_payload_docente())
    assert resp.status_code == 200
    oficio = _oficio(resp)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação\n" in oficio or oficio.rstrip().endswith("Programa: Ciência da Computação")
    assert " - Mestrado" not in oficio
    assert "Participação em evento" not in oficio


def test_link_evento_vazio_remove_linha():
    resp = client.post("/solicitar", json=_payload_valido_alunos(link_evento=""))
    oficio = _oficio(resp)
    assert "Link do evento:" not in oficio
    assert "Complemento:" in oficio


def test_complemento_vazio_remove_linha():
    resp = client.post("/solicitar", json=_payload_valido_alunos(complemento=""))
    oficio = _oficio(resp)
    assert "Complemento:" not in oficio
    assert "Link do evento:" in oficio


def test_campo_obrigatorio_vazio_mostra_mensagem():
    resp = client.post("/solicitar", json=_payload_valido_alunos(nome_completo=""))
    corpo = resp.text
    assert "Preencha todos os campos" in corpo


def test_campo_obrigatorio_vazio_mostra_uma_vez():
    dados = _payload_valido_alunos(nome_completo="", email="", programa="")
    resp = client.post("/solicitar", json=dados)
    corpo = resp.text
    assert corpo.count("Preencha todos os campos") == 1


def test_n_usp_nao_numerico():
    resp = client.post("/solicitar", json=_payload_valido_alunos(n_usp="abc123"))
    assert "N. USP deve conter apenas números" in resp.text


def test_agencia_nao_numerica():
    resp = client.post("/solicitar", json=_payload_valido_alunos(agencia="12a4"))
    assert "Número da agência deve conter apenas números" in resp.text


def test_valor_zero_invalido():
    resp = client.post("/solicitar", json=_payload_valido_alunos(valor_solicitado="0,00"))
    assert "Valor solicitado deve ser maior que 0" in resp.text


def test_email_invalido():
    resp = client.post("/solicitar", json=_payload_valido_alunos(email="maria"))
    assert "E-mail inválido" in resp.text


def test_cpf_formato_invalido():
    resp = client.post("/solicitar", json=_payload_valido_alunos(cpf="12345678909"))
    assert "CPF deve estar no formato 000.000.000-00" in resp.text


def test_cep_formato_invalido():
    resp = client.post("/solicitar", json=_payload_valido_alunos(cep="05508090"))
    assert "CEP deve estar no formato 00000-000" in resp.text


def test_data_formato_invalido():
    resp = client.post("/solicitar", json=_payload_valido_alunos(data_nascimento="01021980"))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resp.text


def test_cpf_digitos_verificadores_invalidos():
    resp = client.post("/solicitar", json=_payload_valido_alunos(cpf="123.456.789-00"))
    assert "CPF inválido" in resp.text


def test_data_inexistente():
    resp = client.post("/solicitar", json=_payload_valido_alunos(data_nascimento="31/02/1980"))
    assert "Data de nascimento inválida" in resp.text


def test_data_mes_invalido():
    resp = client.post("/solicitar", json=_payload_valido_alunos(data_nascimento="01/13/1980"))
    assert "Data de nascimento inválida" in resp.text


def test_multiplos_erros_listados():
    dados = _payload_valido_alunos(n_usp="abc", email="invalido", cpf="123")
    resp = client.post("/solicitar", json=dados)
    corpo = resp.text
    assert "N. USP deve conter apenas números" in corpo
    assert "E-mail inválido" in corpo
    assert "CPF deve estar no formato 000.000.000-00" in corpo


def test_erro_nao_gera_oficio():
    resp = client.post("/solicitar", json=_payload_valido_alunos(nome_completo=""))
    assert "Interessada(o):" not in resp.text


def test_erro_mantem_aba_ativa():
    resp = client.post("/solicitar", json=_payload_valido_alunos(nome_completo="", aba="alunos"))
    corpo = resp.text
    assert "alunos" in corpo.lower()
