"""Testes do envio da solicitação de auxílio financeiro (requisito 01)."""

from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

APELIDOS = {
    "nome": (
        "NOME COMPLETO - SEM ABREVIAR",
        "nome_completo_sem_abreviar",
        "nome_completo",
        "nome",
    ),
    "n_usp": ("N. USP", "n_usp", "nusp", "numero_usp", "num_usp"),
    "programa": ("PROGRAMA", "programa"),
    "nivel": ("NÍVEL", "nivel"),
    "tipo_auxilio": ("TIPO DE AUXÍLIO", "tipo_de_auxilio", "tipo_auxilio"),
    "email": ("E-MAIL", "e_mail", "email"),
    "evento": (
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "nome_do_evento_banca_de_exame_ou_defesa",
        "nome_evento",
        "evento",
    ),
    "periodo": (
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "periodo_do_evento_exame_ou_defesa",
        "periodo_evento",
        "periodo",
    ),
    "cidade_evento": (
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "cidade_do_evento_exame_ou_defesa",
        "cidade_evento",
    ),
    "estado_evento": (
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "estado_do_evento_exame_ou_defesa",
        "estado_evento",
    ),
    "pais_evento": (
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "pais_do_evento_exame_ou_defesa",
        "pais_evento",
    ),
    "link_evento": (
        "LINK DO EVENTO, EXAME OU DEFESA",
        "link_do_evento_exame_ou_defesa",
        "link_evento",
    ),
    "valor": ("VALOR SOLICITADO (R$)", "valor_solicitado", "valor"),
    "detalhamento": ("DETALHAMENTO DO PEDIDO", "detalhamento_do_pedido", "detalhamento"),
    "apresentacao": (
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "ira_apresentar_trabalho_no_evento_que_tipo",
        "apresentacao_trabalho",
        "apresentacao",
    ),
    "data_nascimento": ("DATA DE NASCIMENTO", "data_de_nascimento", "data_nascimento"),
    "logradouro": ("LOGRADOURO", "logradouro"),
    "numero": ("NÚMERO", "numero"),
    "complemento": ("COMPLEMENTO", "complemento"),
    "bairro": ("BAIRRO", "bairro"),
    "cep": ("CEP", "cep"),
    "cidade": ("CIDADE", "cidade"),
    "estado": ("ESTADO", "estado"),
    "cpf": ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "cpf_separados_por_pontos_e_traco", "cpf"),
    "rg": (
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "rg_rnm_separados_por_pontos_e_traco",
        "rg_rnm",
        "rg",
    ),
    "banco": ("NOME DO BANCO", "nome_do_banco", "banco"),
    "agencia": ("NÚMERO DA AGÊNCIA", "numero_da_agencia", "agencia"),
    "conta": ("NÚMERO DA CONTA", "numero_da_conta", "conta"),
}


def _rotas_de_envio():
    rotas = []
    for rota in app.routes:
        metodos = getattr(rota, "methods", None)
        if metodos and "POST" in metodos and not rota.path.startswith(("/docs", "/redoc", "/openapi")):
            rotas.append(rota.path)
    assert rotas, "a aplicação não expõe rota POST para o envio da solicitação"
    return rotas


def _enviar(valores, extras=None, caminho=None):
    corpo = {}
    for campo, apelidos in APELIDOS.items():
        for apelido in apelidos:
            corpo[apelido] = valores.get(campo, "")
    padrao = {"aba": "ALUNOS", "tipo_solicitante": "ALUNOS", "formulario": "ALUNOS"}
    for chave, valor in {**padrao, **(extras or {})}.items():
        corpo[chave] = valor
    destino = caminho or _rotas_de_envio()[0]
    resposta = cliente.post(destino, json=corpo)
    if resposta.status_code == 422 and "Field required" in resposta.text:
        resposta = cliente.post(destino, data=corpo)
    return resposta


def solicitacao_aluno(**mudancas):
    valores = {
        "nome": "Fulana de Tal",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "fulana@ime.usp.br",
        "evento": "Congresso Brasileiro de Computação",
        "periodo": "10/07/2025 a 15/07/2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.example.com",
        "valor": "R$ 1.500,00",
        "detalhamento": "Passagens aéreas e hospedagem",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "529.982.247-25",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    valores.update(mudancas)
    return valores


def test_envio_valido_devolve_o_oficio_com_os_dados_da_aba_de_alunos():
    texto = _enviar(solicitacao_aluno()).text
    assert "Interessada(o): Fulana de Tal - 12345678" in texto
    assert "E-mail: fulana@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Rua do Matão, 1010" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "CPF: 529.982.247-25" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto


def test_linhas_dos_campos_opcionais_vazios_saem_do_oficio():
    texto = _enviar(solicitacao_aluno(link_evento="", complemento="")).text
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_oficio_da_aba_de_docentes_usa_a_verba_do_programa():
    dados = solicitacao_aluno()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    combinacoes = [{}]
    for chave in ("aba", "tipo_solicitante", "formulario", "tab"):
        for valor in ("DOCENTES", "docentes"):
            combinacoes.append({chave: valor})
    for caminho in _rotas_de_envio():
        for extras in combinacoes:
            texto = _enviar(dados, extras, caminho).text
            if "Verba do programa" in texto:
                assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
                assert "Programa: Ciência da Computação" in texto
                return
    raise AssertionError("o ofício da aba DOCENTES deve usar 'Verba do programa'")


def test_campo_obrigatorio_vazio_pede_preenchimento():
    texto = _enviar({}).text
    assert texto.count("Preencha todos os campos") == 1
    assert "Encaminhe-se ao Serviço Financeiro para providências." not in texto


def test_n_usp_so_com_digitos():
    texto = _enviar(solicitacao_aluno(n_usp="12A45678")).text
    assert "N. USP deve conter apenas números" in texto


def test_numero_da_agencia_so_com_digitos():
    texto = _enviar(solicitacao_aluno(agencia="12-34")).text
    assert "Número da agência deve conter apenas números" in texto


def test_valor_solicitado_maior_que_zero():
    texto = _enviar(solicitacao_aluno(valor="0")).text
    assert "Valor solicitado deve ser maior que 0" in texto


def test_email_precisa_de_arroba_e_dominio():
    texto = _enviar(solicitacao_aluno(email="fulana.ime.usp.br")).text
    assert "E-mail inválido" in texto


def test_cpf_fora_do_formato_000_000_000_00():
    texto = _enviar(solicitacao_aluno(cpf="529.982.247")).text
    assert "CPF deve estar no formato 000.000.000-00" in texto


def test_cep_fora_do_formato_00000_000():
    texto = _enviar(solicitacao_aluno(cep="05508-09")).text
    assert "CEP deve estar no formato 00000-000" in texto


def test_data_de_nascimento_fora_do_formato_dd_mm_aaaa():
    texto = _enviar(solicitacao_aluno(data_nascimento="01-02-1980")).text
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto


def test_cpf_com_digitos_verificadores_invalidos():
    texto = _enviar(solicitacao_aluno(cpf="123.456.789-00")).text
    assert "CPF inválido" in texto


def test_data_de_nascimento_inexistente():
    texto = _enviar(solicitacao_aluno(data_nascimento="31/02/1980")).text
    assert "Data de nascimento inválida" in texto
