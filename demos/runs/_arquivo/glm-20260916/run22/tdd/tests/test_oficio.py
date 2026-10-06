ROTA = "/api/solicitacao"


def _linhas(texto):
    return [linha.strip() for linha in texto.splitlines()]


def test_oficio_da_aba_alunos(client, dados_alunos, oficio_esperado):
    corpo = client.post(ROTA, =dados_alunos).()
    assert _linhas(corpo["oficio"]) == oficio_esperado(dados_alunos)


def test_oficio_da_aba_docentes(client, dados_docentes, oficio_esperado):
    corpo = client.post(ROTA, =dados_docentes).()
    linhas = _linhas(corpo["oficio"])
    assert linhas == oficio_esperado(dados_docentes)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in linhas
    assert not any("Mestrado" in linha for linha in linhas)


def test_valor_no_oficio_formatado_com_milhar(client, dados_alunos):
    dados = {**dados_alunos, "VALOR SOLICITADO (R$)": "R$ 1.500.000,00"}
    corpo = client.post(ROTA, =dados).()
    assert "Valor solicitado: R$ 1.500.000,00" in _linhas(corpo["oficio"])


def test_campos_opcionais_vazios_saem_do_oficio(client, dados_alunos, oficio_esperado):
    dados = {**dados_alunos, "LINK DO EVENTO, EXAME OU DEFESA": "", "COMPLEMENTO": ""}
    corpo = client.post(ROTA, =dados).()
    linhas = _linhas(corpo["oficio"])
    assert not any(linha.startswith("Link do evento") for linha in linhas)
    assert not any(linha.startswith("Complemento") for linha in linhas)
    assert linhas == oficio_esperado(dados)
