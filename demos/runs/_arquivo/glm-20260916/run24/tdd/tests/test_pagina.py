ROTULOS_COMPARTILHADOS = (
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
)

ROTULOS_SOMENTE_ALUNOS = ("NÍVEL", "TIPO DE AUXÍLIO")

TITULOS_DE_BLOCO = (
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
)

OPCOES = (
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
)


def test_pagina_inicial_e_servida(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers.get("content-type", "")


def test_abas_alunos_e_docentes_nessa_ordem(pagina):
    assert pagina.count("ALUNOS") >= 1
    assert pagina.count("DOCENTES") >= 1
    assert pagina.find("ALUNOS") < pagina.find("DOCENTES")


def test_titulos_dos_blocos_nas_duas_abas(pagina):
    for titulo in TITULOS_DE_BLOCO:
        assert pagina.count(titulo) == 2, titulo


def test_rotulos_compartilhados_nas_duas_abas(pagina):
    for rotulo in ROTULOS_COMPARTILHADOS:
        assert pagina.count(rotulo) >= 2, rotulo


def test_rotulos_exclusivos_da_aba_alunos_aparecem_poucas_vezes(pagina):
    for rotulo in ROTULOS_SOMENTE_ALUNOS:
        assert pagina.count(rotulo) <= 2, rotulo


def test_nivel_e_tipo_de_auxilio_so_no_formulario_de_alunos(elementos):
    formularios = [texto for tag, _, texto in elementos if tag == "form"]
    if len(formularios) == 2:
        assert sum("NÍVEL" in texto for texto in formularios) == 1
        assert sum("TIPO DE AUXÍLIO" in texto for texto in formularios) == 1


def test_opcoes_das_selecoes(pagina):
    for opcao in OPCOES:
        assert opcao in pagina, opcao


def test_botao_enviar_solicitacao_em_cada_aba(pagina):
    assert pagina.count("Enviar solicitação") == 2


def test_cabecalho_institucional(pagina, elementos):
    assert "Universidade de São Paulo" in pagina
    origens = [attrs.get("src", "") for tag, attrs, _ in elementos if tag == "img"]
    assert any("usp-logo" in origem for origem in origens), (
        "o logotipo da USP não está no cabeçalho"
    )


def test_logotipo_referenciado_e_servido(client, elementos):
    origens = [
        attrs.get("src", "")
        for tag, attrs, _ in elementos
        if tag == "img" and "usp-logo" in attrs.get("src", "")
    ]
    assert origens
    for origem in origens:
        caminho = origem if origem.startswith("/") else "/" + origem
        resposta = client.get(caminho)
        assert resposta.status_code == 200
        assert resposta.headers.get("content-type", "").startswith("image")


def test_pasta_de_assets_e_servida(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200


def test_nenhuma_imagem_alem_do_logotipo(pagina, elementos):
    origens = [attrs.get("src", "") for tag, attrs, _ in elementos if tag == "img"]
    assert all("usp-logo" in origem for origem in origens)
    assert "brasao" not in pagina.lower()


def test_todo_campo_tem_placeholder_que_nao_repete_o_rotulo(elementos):
    campos = [attrs for tag, attrs, _ in elementos if tag in ("input", "textarea")]
    assert len(campos) >= 50, "faltam campos do formulário na página"
    rotulos = {rotulo.lower() for rotulo in ROTULOS_COMPARTILHADOS + ROTULOS_SOMENTE_ALUNOS}
    for attrs in campos:
        placeholder = (attrs.get("placeholder") or "").strip()
        assert placeholder, f"campo sem placeholder: {attrs}"
        assert placeholder.lower() not in rotulos, (
            f"placeholder repete o rótulo: {placeholder}"
        )


def test_nenhum_recurso_vindo_da_rede(elementos):
    for tag, attrs, _ in elementos:
        folha = tag == "link" and "stylesheet" in (attrs.get("rel") or "").lower()
        if tag in ("img", "script") or folha:
            origem = attrs.get("src") or attrs.get("href") or ""
            if origem:
                assert not origem.startswith(("http://", "https://", "//")), (
                    f"recurso remoto: {origem}"
                )


def test_cores_da_identidade_da_usp(css):
    minusculo = css.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in minusculo, cor


def test_fonte_sem_serifa(css):
    assert "sans-serif" in css.lower()


def test_oficio_preserva_quebras_de_linha(css, appjs, pagina):
    todo = (pagina + css + appjs).lower()
    assert (
        "pre-wrap" in todo
        or "<pre" in todo
        or ("\\n" in appjs and "<br" in appjs.lower())
    ), "nada indica que as quebras de linha do ofício são preservadas"


def test_aba_ativa_e_distinguivel_da_inativa(elementos, appjs):
    classes = {}
    for tag, attrs, texto in elementos:
        if texto in ("ALUNOS", "DOCENTES"):
            classes[texto] = attrs.get("class", "")
    if classes.get("ALUNOS") and classes.get("ALUNOS") != classes.get("DOCENTES"):
        return
    javascript = appjs.lower()
    assert any(
        sinal in javascript
        for sinal in ("classlist", "classname", "class=", "setattribute")
    ), "não há como a aba ativa ficar visualmente distinguível da inativa"
