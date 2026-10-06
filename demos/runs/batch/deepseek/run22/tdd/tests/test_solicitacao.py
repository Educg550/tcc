CAMPOS_OBRIGATORIOS = "Preencha todos os campos"

CAMINHOS = ("/api/solicitacao", "/solicitacao", "/api/solicitar", "/api/oficio")


def _dados_alunos(**mudancas):
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria Aparecida da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro de Computação",
        "periodo_evento": "10 a 15 de outubro de 2025",
        "cidade_evento": "Florianópolis",
        "estado_evento": "SC",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.exemplo.br/",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento": "Passagem aérea e hospedagem.",
        "apresentacao_trabalho": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    for chave, valor in mudancas.items():
        if valor is None:
            dados.pop(chave, None)
        else:
            dados[chave] = valor
    return dados


def _dados_docentes(**mudancas):
    return _dados_alunos(aba="docentes", nivel=None, tipo_auxilio=None, **mudancas)


def _dados_vazios():
    dados = {chave: "" for chave in _dados_alunos()}
    dados["aba"] = "alunos"
    return dados


def _enviar(cliente, dados):
    for caminho in CAMINHOS:
        resposta = cliente.post(caminho, json=dados)
        if resposta.status_code != 404:
            return resposta
    raise AssertionError("nenhum endpoint de solicitação respondeu")


def _textos(valor):
    if isinstance(valor, str):
        return [valor]
    if isinstance(valor, dict):
        return [texto for item in valor.values() for texto in _textos(item)]
    if isinstance(valor, list):
        return [texto for item in valor for texto in _textos(item)]
    return []


def _mensagens(resposta):
    try:
        corpo = resposta.json()
    except ValueError:
        corpo = resposta.text
    return _textos(corpo)


def _contem(resposta, mensagem):
    return any(mensagem in texto for texto in _mensagens(resposta))


def _tem_oficio(resposta):
    return any("Interessada(o):" in texto for texto in _mensagens(resposta))


def _oficio(resposta):
    for texto in _mensagens(resposta):
        if "Interessada(o):" in texto:
            return texto
    raise AssertionError(f"ofício não encontrado na resposta: {resposta.text}")


def _linhas(texto):
    return [linha.strip() for linha in texto.splitlines() if linha.strip()]


def _sem_linhas(texto, prefixos):
    return "\n".join(
        linha
        for linha in texto.splitlines()
        if not any(linha.startswith(prefixo) for prefixo in prefixos)
    )


def _oficio_esperado(dados, assunto, programa):
    return f"""Interessada(o): {dados['nome_completo']} - {dados['n_usp']}
E-mail: {dados['email']}
Assunto: {assunto}
Programa: {programa}

A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {dados['nome_evento']}
Período: {dados['periodo_evento']}
Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}
Link do evento: {dados['link_evento']}
Apresentação de trabalho: {dados['apresentacao_trabalho']}
Valor solicitado: {dados['valor_solicitado']}
Detalhamento: {dados['detalhamento']}

Endereço da(o) interessada(o)
{dados['logradouro']}, {dados['numero']}
Complemento: {dados['complemento']}
CEP: {dados['cep']}
{dados['bairro']}, {dados['cidade']} - {dados['estado']}

Dados para pagamento
Data de nascimento: {dados['data_nascimento']}
CPF: {dados['cpf']}
RG / RNM: {dados['rg']}
Banco: {dados['banco']}
Agência: {dados['agencia']}
Conta: {dados['conta']}

Encaminhe-se ao Serviço Financeiro para providências."""


def _assunto_e_programa_dos_alunos(dados):
    return (
        f"Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}",
        f"{dados['programa']} - {dados['nivel']}",
    )


def _erro_esperado(resposta, mensagem):
    assert _contem(resposta, mensagem), resposta.text
    assert not _tem_oficio(resposta)


def test_oficio_da_aba_alunos(cliente):
    dados = _dados_alunos()
    resposta = _enviar(cliente, dados)
    assert resposta.status_code == 200
    assunto, programa = _assunto_e_programa_dos_alunos(dados)
    esperado = _oficio_esperado(dados, assunto, programa)
    assert _linhas(_oficio(resposta)) == _linhas(esperado)


def test_oficio_da_aba_docentes(cliente):
    dados = _dados_docentes()
    resposta = _enviar(cliente, dados)
    assert resposta.status_code == 200
    esperado = _oficio_esperado(
        dados,
        "Solicitação de Auxílio Financeiro - Verba do programa",
        dados["programa"],
    )
    assert _linhas(_oficio(resposta)) == _linhas(esperado)


def test_link_e_complemento_vazios_saem_do_oficio(cliente):
    dados = _dados_alunos(link_evento="", complemento="")
    resposta = _enviar(cliente, dados)
    assunto, programa = _assunto_e_programa_dos_alunos(dados)
    esperado = _sem_linhas(
        _oficio_esperado(dados, assunto, programa),
        ("Link do evento:", "Complemento:"),
    )
    assert _linhas(_oficio(resposta)) == _linhas(esperado)


def test_todos_os_campos_vazios(cliente):
    resposta = _enviar(cliente, _dados_vazios())
    ocorrencias = sum(
        texto.count(CAMPOS_OBRIGATORIOS) for texto in _mensagens(resposta)
    )
    assert ocorrencias == 1
    assert not _tem_oficio(resposta)


def test_n_usp_precisa_ser_so_digitos(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(n_usp="12A45678")),
        "N. USP deve conter apenas números",
    )


def test_agencia_precisa_ser_so_digitos(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(agencia="12-34")),
        "Número da agência deve conter apenas números",
    )


def test_valor_solicitado_precisa_ser_maior_que_zero(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(valor_solicitado="R$ 0,00")),
        "Valor solicitado deve ser maior que 0",
    )


def test_email_invalido(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(email="maria.ime.usp.br")),
        "E-mail inválido",
    )


def test_cpf_fora_do_formato(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(cpf="12345678909")),
        "CPF deve estar no formato 000.000.000-00",
    )


def test_cep_fora_do_formato(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(cep="05508090")),
        "CEP deve estar no formato 00000-000",
    )


def test_data_de_nascimento_fora_do_formato(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(data_nascimento="1980-02-01")),
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    )


def test_cpf_com_digitos_verificadores_invalidos(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(cpf="123.456.789-00")),
        "CPF inválido",
    )


def test_data_de_nascimento_inexistente(cliente):
    _erro_esperado(
        _enviar(cliente, _dados_alunos(data_nascimento="31/02/1980")),
        "Data de nascimento inválida",
    )


def test_varios_erros_de_uma_vez(cliente):
    dados = _dados_alunos(n_usp="12A45678", agencia="12-34", email="maria.ime.usp.br")
    resposta = _enviar(cliente, dados)
    assert _contem(resposta, "N. USP deve conter apenas números")
    assert _contem(resposta, "Número da agência deve conter apenas números")
    assert _contem(resposta, "E-mail inválido")
    assert not _tem_oficio(resposta)
