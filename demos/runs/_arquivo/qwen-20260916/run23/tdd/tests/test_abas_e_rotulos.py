def _html(client):
    return client.get("/").text


def test_abas_na_ordem(client):
    t = _html(client)
    assert t.index("ALUNOS") < t.index("DOCENTES")


def test_abra_com_alunos_ativa(client):
    t = _html(client)
    alunos = t.index("ALUNOS")
    docentes = t.index("DOCENTES")
    ativa = t.index("active", max(0, alunos - 400))
    assert ativa < docentes, "aba ALUNOS deve ser a ativa ao abrir"


def test_dois_botoes_enviar(client):
    assert _html(client).count("Enviar solicitação") == 2


def test_titulos_dos_blocos(client):
    t = _html(client)
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in t


def test_campo_exclusivo_alunos(client):
    t = _html(client)
    assert t.count("NÍVEL") == 1
    assert t.count("TIPO DE AUXÍLIO") == 1
    assert "Banca de exame ou defesa" in t


def test_campo_docentes_nao_replica_exclusivos(client):
    t = _html(client)
    assert t.index("NÍVEL") < t.index("DOCENTES")
    assert t.index("TIPO DE AUXÍLIO") < t.index("DOCENTES")


def test_campos_em_duplicata(client):
    t = _html(client)
    for rotulo in (
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    ):
        assert t.count(rotulo) == 2, rotulo


def test_opcoes_apresentacao(client):
    t = _html(client)
    for opcao in ("Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"):
        assert t.count(opcao) == 2, opcao


def test_campos_formataveis(client):
    t = _html(client)
    for rotulo in ("DATA DE NASCIMENTO", "CEP", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"):
        assert t.count(rotulo) == 2, rotulo
