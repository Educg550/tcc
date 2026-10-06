import os

TRECHOS_DO_OFICIO = (
    "Interessada(o): Maria Souza da Silva - 1234567",
    "E-mail: maria@ime.usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "Dados do evento",
    "Evento: Congresso Brasileiro de Computação",
    "Período: 10/03/2025 a 14/03/2025",
    "Local: Campinas - SP - Brasil",
    "Link do evento: https://cmyc.ime.usp.br",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição no evento e passagem aérea",
    "Endereço da(o) interessada(o)",
    "Rua do Anfiteatro, 181",
    "Complemento: Sala 212",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 529.982.247-25",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 98765-4",
    "Encaminhe-se ao Serviço Financeiro para providências.",
)


def test_envio_valido_de_aluno_gera_o_oficio_preenchido(
    achar_resposta, solicitacao_alunos, pagina, appjs
):
    resposta = achar_resposta(solicitacao_alunos, TRECHOS_DO_OFICIO)
    assert resposta is not None, (
        "o backend não devolveu o ofício da solicitação válida de aluno"
    )
    assert "Solicitação registrada" in (pagina + appjs + resposta.text)


def test_envio_valido_de_docente_gera_o_oficio_de_docente(
    achar_resposta, solicitacao_docentes
):
    resposta = achar_resposta(
        solicitacao_docentes,
        (
            "Interessada(o): Maria Souza da Silva - 1234567",
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            "Programa: Ciência da Computação",
            "Valor solicitado: R$ 1.500,00",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ),
    )
    assert resposta is not None, (
        "o backend não devolveu o ofício da solicitação válida de docente"
    )
    assert "Mestrado" not in resposta.text
    assert "Participação em evento" not in resposta.text


def test_campos_opcionais_vazios_geram_oficio_sem_as_linhas(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        remover=(
            "link_do_evento",
            "link",
            "linkDoEvento",
            "LINK DO EVENTO, EXAME OU DEFESA",
            "complemento",
            "COMPLEMENTO",
        ),
    )
    resposta = achar_resposta(
        payload,
        (
            "Interessada(o): Maria Souza da Silva - 1234567",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ),
    )
    assert resposta is not None
    assert "Link do evento" not in resposta.text
    assert "Complemento" not in resposta.text
    assert "Preencha todos os campos" not in resposta.text


def test_solicitacao_totalmente_vazia(achar_resposta):
    resposta = achar_resposta({}, ("Preencha todos os campos",))
    assert resposta is not None
    assert resposta.text.count("Preencha todos os campos") == 1
    assert "Encaminhe-se ao Serviço Financeiro" not in resposta.text


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        remover=("nome_completo", "nome", "nomeCompleto", "NOME COMPLETO - SEM ABREVIAR"),
    )
    resposta = achar_resposta(payload, ("Preencha todos os campos",))
    assert resposta is not None
    assert resposta.text.count("Preencha todos os campos") == 1
    assert "Encaminhe-se ao Serviço Financeiro" not in resposta.text


def test_n_usp_deve_conter_apenas_numeros(achar_resposta, solicitacao_alunos, alterar):
    payload = alterar(
        solicitacao_alunos,
        {
            "n_usp": "12A3456",
            "numero_usp": "12A3456",
            "nUSP": "12A3456",
            "numeroUSP": "12A3456",
            "N. USP": "12A3456",
        },
    )
    resposta = achar_resposta(payload, ("N. USP deve conter apenas números",))
    assert resposta is not None


def test_numero_da_agencia_deve_conter_apenas_numeros(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        {
            "agencia": "12A4",
            "numero_da_agencia": "12A4",
            "numeroDaAgencia": "12A4",
            "NÚMERO DA AGÊNCIA": "12A4",
        },
    )
    resposta = achar_resposta(payload, ("Número da agência deve conter apenas números",))
    assert resposta is not None


def test_valor_solicitado_deve_ser_maior_que_zero(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        {
            "valor_solicitado": "R$ 0,00",
            "valor": "R$ 0,00",
            "valorSolicitado": "R$ 0,00",
            "VALOR SOLICITADO (R$)": "R$ 0,00",
        },
    )
    resposta = achar_resposta(payload, ("Valor solicitado deve ser maior que 0",))
    assert resposta is not None


def test_email_invalido(achar_resposta, solicitacao_alunos, alterar):
    payload = alterar(
        solicitacao_alunos,
        {"email": "maria.usp.br", "e_mail": "maria.usp.br", "E-MAIL": "maria.usp.br"},
    )
    resposta = achar_resposta(payload, ("E-mail inválido",))
    assert resposta is not None
    assert "Encaminhe-se ao Serviço Financeiro" not in resposta.text


def test_cpf_fora_do_formato(achar_resposta, solicitacao_alunos, alterar):
    payload = alterar(
        solicitacao_alunos,
        {"cpf": "52998224725", "CPF (SEPARADOS POR PONTOS E TRAÇO)": "52998224725"},
    )
    resposta = achar_resposta(payload, ("CPF deve estar no formato 000.000.000-00",))
    assert resposta is not None
    assert "CPF inválido" not in resposta.text


def test_cep_fora_do_formato(achar_resposta, solicitacao_alunos, alterar):
    payload = alterar(solicitacao_alunos, {"cep": "05508090", "CEP": "05508090"})
    resposta = achar_resposta(payload, ("CEP deve estar no formato 00000-000",))
    assert resposta is not None


def test_data_de_nascimento_fora_do_formato(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        {
            "data_de_nascimento": "01021980",
            "data_nascimento": "01021980",
            "dataDeNascimento": "01021980",
            "DATA DE NASCIMENTO": "01021980",
        },
    )
    resposta = achar_resposta(
        payload, ("Data de nascimento deve estar no formato dd/mm/aaaa",)
    )
    assert resposta is not None


def test_cpf_com_digito_verificador_errado(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        {"cpf": "529.982.247-00", "CPF (SEPARADOS POR PONTOS E TRAÇO)": "529.982.247-00"},
    )
    resposta = achar_resposta(payload, ("CPF inválido",))
    assert resposta is not None
    assert "CPF deve estar no formato 000.000.000-00" not in resposta.text


def test_data_de_nascimento_inexistente(achar_resposta, solicitacao_alunos, alterar):
    payload = alterar(
        solicitacao_alunos,
        {
            "data_de_nascimento": "31/02/1980",
            "data_nascimento": "31/02/1980",
            "dataDeNascimento": "31/02/1980",
            "DATA DE NASCIMENTO": "31/02/1980",
        },
    )
    resposta = achar_resposta(payload, ("Data de nascimento inválida",))
    assert resposta is not None
    assert "deve estar no formato" not in resposta.text


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(
    achar_resposta, solicitacao_alunos, alterar
):
    payload = alterar(
        solicitacao_alunos,
        {
            "email": "maria.usp.br",
            "e_mail": "maria.usp.br",
            "E-MAIL": "maria.usp.br",
            "cpf": "52998224725",
            "CPF (SEPARADOS POR PONTOS E TRAÇO)": "52998224725",
            "cep": "05508090",
            "CEP": "05508090",
        },
    )
    resposta = achar_resposta(
        payload,
        (
            "E-mail inválido",
            "CPF deve estar no formato 000.000.000-00",
            "CEP deve estar no formato 00000-000",
        ),
    )
    assert resposta is not None
    assert "Preencha todos os campos" not in resposta.text
    assert "Encaminhe-se ao Serviço Financeiro" not in resposta.text


def arquivos_do_projeto():
    registro = {}
    for raiz, pastas, nomes in os.walk("."):
        pastas[:] = [
            pasta
            for pasta in pastas
            if pasta not in ("__pycache__", ".pytest_cache", ".git")
        ]
        for nome in nomes:
            if nome.endswith(".pyc"):
                continue
            caminho = os.path.join(raiz, nome)
            try:
                with open(caminho, "rb") as arquivo:
                    registro[caminho] = len(arquivo.read())
            except OSError:
                registro[caminho] = -1
    return registro


def test_nada_e_gravado_em_arquivo(enviar, solicitacao_alunos):
    antes = arquivos_do_projeto()
    enviar(solicitacao_alunos)
    enviar({})
    assert arquivos_do_projeto() == antes
