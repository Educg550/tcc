import re
from tests.conftest import client


def _aluno_valido():
    return {
        "aba": "ALUNOS",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@usp.br",
        "nome_evento": "SBC 2025",
        "periodo_evento": "10 a 15 de outubro",
        "cidade_evento": "Florianópolis",
        "estado_evento": "SC",
        "pais_evento": "Brasil",
        "link_evento": "https://sbc.org.br",
        "valor_solicitado": "150000",
        "detalhamento": "Participar com trabalho",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01021980",
        "logradouro": "Rua A",
        "numero": "123",
        "complemento": "Apto 1",
        "bairro": "Centro",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def _docente_valido():
    d = _aluno_valido()
    d["aba"] = "DOCENTES"
    d.pop("nivel")
    d.pop("tipo_auxilio")
    return d


# ---- ABAS E ESTRUTURA ----

def test_abas_existem_na_ordem():
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "ALUNOS" in body
    assert "DOCENTES" in body
    assert body.index("ALUNOS") < body.index("DOCENTES")


def test_abas_tem_ruidos_visiveis_com_rotulos_exatos():
    body = client.get("/").text
    assert re.search(r">\s*ALUNOS\s*<", body)
    assert re.search(r">\s*DOCENTES\s*<", body)


def test_titulo_pagina():
    body = client.get("/").text
    assert "auxílio financeiro" in body.lower()


def test_rotulos_exatos_de_campos():
    body = client.get("/").text
    rotulos = [
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
    ]
    for r in rotulos:
        assert r in body, f"Rótulo ausente: {r}"


def test_placeholder_visivel_para_cada_campo():
    body = client.get("/").text
    assert body.count("placeholder=") >= 30
    # placeholder não pode ser a repetição do rótulo do campo
    assert 'placeholder="NOME COMPLETO' not in body


def test_campos_selecao_alunos():
    body = client.get("/").text
    for opcao in ("Mestrado", "Doutorado", "Participação em evento",
                  "Banca de exame ou defesa", "Outro", "Pôster",
                  "Apresentação oral", "Não irá apresentar trabalho"):
        assert opcao in body, f"Opção ausente: {opcao}"


def test_docentes_nao_tem_nivel_nem_tipo_auxilio():
    body = client.get("/").text
    # as duas abas têm os mesmos campos exceto NÍVEL e TIPO DE AUXÍLIO,
    # que aparecem uma única vez (somente na aba ALUNOS)
    assert body.count("NÍVEL") == 1
    assert body.count("TIPO DE AUXÍLIO") == 1


def test_duas_abas_tem_dois_botoes_enviar():
    body = client.get("/").text
    assert body.count("Enviar solicitação") == 2


# ---- APARÊNCIA ----

def test_css_serve():
    r = client.get("/style.css")
    assert r.status_code == 200
    assert "text/css" in r.headers["content-type"]


def test_js_serve():
    r = client.get("/app.js")
    assert r.status_code == 200


def test_css_sem_framework():
    css = client.get("/style.css").text
    assert css.strip()
    for proibido in ("bootstrap", "tailwind", "cdn", "@import http"):
        assert proibido not in css.lower()


def test_core_identidade_usp_no_css():
    css = client.get("/style.css").text.lower()
    assert "1094ab" in css
    assert "64c4d2" in css
    assert "fcb421" in css


def test_css_fonte_sem_serifa():
    css = client.get("/style.css").text.lower()
    assert "open sans" in css or "sans-serif" in css


def test_css_nao_importa_remoto():
    css = client.get("/style.css").text
    assert "http" not in css.lower()


def test_js_formatadores_presentes():
    js = client.get("/app.js").text
    assert js.strip()
    assert "R$" in js
    assert "blur" in js.lower()


def test_js_sem_dependencia_remota():
    js = client.get("/app.js").text
    assert "http" not in js.lower()


def test_logo_serve():
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200


def test_logo_presente_e_sem_brasao():
    body = client.get("/").text
    assert "usp-logo.png" in body
    assert "Universidade de São Paulo" in body


def test_brasao_nao_aparece():
    body = client.get("/").text
    for termo in ("brasao", "escudo", "coat"):
        assert termo not in body.lower()
    css = client.get("/style.css").text.lower()
    for termo in ("brasao", "escudo", "coat"):
        assert termo not in css


# ---- VALIDAÇÃO BACKEND ----

def test_campos_obrigatorios_vazio_gera_erro():
    d = _aluno_valido()
    d["nome_completo"] = ""
    r = client.post("/solicitacao", json=d)
    assert r.status_code == 200
    corpo = r.json()
    assert "erros" in corpo
    assert "Preencha todos os campos" in corpo["erros"]
    assert "oficio" not in corpo


def test_mensagem_preencha_uma_unica_vez():
    d = _aluno_valido()
    d["nome_completo"] = ""
    d["programa"] = ""
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert erros.count("Preencha todos os campos") == 1


def test_nusp_so_digitos():
    d = _aluno_valido()
    d["n_usp"] = "12a34"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "N. USP deve conter apenas números" in erros


def test_agencia_so_digitos():
    d = _aluno_valido()
    d["agencia"] = "1a2"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "Número da agência deve conter apenas números" in erros


def test_valor_natural_maior_que_zero():
    d = _aluno_valido()
    d["valor_solicitado"] = "0"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "Valor solicitado deve ser maior que 0" in erros


def test_valor_negativo_rejeitado():
    d = _aluno_valido()
    d["valor_solicitado"] = "-1"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "Valor solicitado deve ser maior que 0" in erros


def test_email_sem_arroba():
    d = _aluno_valido()
    d["email"] = "maria.usp.br"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "E-mail inválido" in erros


def test_email_sem_dominio():
    d = _aluno_valido()
    d["email"] = "maria@"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "E-mail inválido" in erros


def test_cpf_fora_formato():
    d = _aluno_valido()
    d["cpf"] = "12345678909"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_cep_fora_formato():
    d = _aluno_valido()
    d["cep"] = "05508090"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_nascimento_fora_formato():
    d = _aluno_valido()
    d["data_nascimento"] = "01021980"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_cpf_digito_verificador_invalido():
    d = _aluno_valido()
    d["cpf"] = "111.111.111-11"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "CPF inválido" in erros


def test_data_nascimento_inexistente():
    d = _aluno_valido()
    d["data_nascimento"] = "31/02/1980"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "Data de nascimento inválida" in erros


def test_mes_fora_faixa():
    d = _aluno_valido()
    d["data_nascimento"] = "01/13/1980"
    erros = client.post("/solicitacao", json=d).json()["erros"]
    assert "Data de nascimento inválida" in erros


def test_com_erro_nao_gera_oficio():
    d = _aluno_valido()
    d["email"] = "invalido"
    corpo = client.post("/solicitacao", json=d).json()
    assert corpo.get("oficio") in (None, "")


# ---- ENVIO VÁLIDO / OFÍCIO ALUNOS ----

def test_envio_valido_aluno_sem_erros():
    corpo = client.post("/solicitacao", json=_aluno_valido()).json()
    assert corpo.get("erros") in (None, [])
    assert "oficio" in corpo


def test_rotulo_confirmacao():
    corpo = client.post("/solicitacao", json=_aluno_valido()).json()
    assert "oficio" in corpo


def test_oficio_aluno_dados_evento():
    oficio = client.post("/solicitacao", json=_aluno_valido()).json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Doutorado" in oficio
    assert "Dados do evento" in oficio
    assert "Evento: SBC 2025" in oficio
    assert "Período: 10 a 15 de outubro" in oficio
    assert "Local: Florianópolis - SC - Brasil" in oficio
    assert "Link do evento: https://sbc.org.br" in oficio
    assert "Apresentação de trabalho: Apresentação oral" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Participar com trabalho" in oficio


def test_oficio_aluno_dados_endereco_pagamento():
    oficio = client.post("/solicitacao", json=_aluno_valido()).json()["oficio"]
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Rua A, 123" in oficio
    assert "Complemento: Apto 1" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Centro, São Paulo - SP" in oficio
    assert "Dados para pagamento" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_preserva_quebras_linha():
    oficio = client.post("/solicitacao", json=_aluno_valido()).json()["oficio"]
    assert "\n" in oficio


def test_link_evento_vazio_sai_linha():
    d = _aluno_valido()
    d["link_evento"] = ""
    oficio = client.post("/solicitacao", json=d).json()["oficio"]
    assert "Link do evento" not in oficio


def test_complemento_vazio_sai_linha():
    d = _aluno_valido()
    d["complemento"] = ""
    oficio = client.post("/solicitacao", json=d).json()["oficio"]
    assert "Complemento:" not in oficio


# ---- OFÍCIO DOCENTES ----

def test_oficio_docente_assunto_programa():
    oficio = client.post("/solicitacao", json=_docente_valido()).json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação\n" in oficio


def test_oficio_docente_sem_nivel():
    oficio = client.post("/solicitacao", json=_docente_valido()).json()["oficio"]
    assert "- Doutorado" not in oficio


def test_oficio_docente_restante_igual():
    oficio = client.post("/solicitacao", json=_docente_valido()).json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "Banco: Banco do Brasil" in oficio


def test_valor_formatado_centavos():
    d = _aluno_valido()
    d["valor_solicitado"] = "1500"
    oficio = client.post("/solicitacao", json=d).json()["oficio"]
    assert "Valor solicitado: R$ 15,00" in oficio
