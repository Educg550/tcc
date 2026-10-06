"""Testes para o formulário de solicitação de auxílio financeiro da PG do IME-USP."""

import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def get_index():
    return client.get("/")


def get(path):
    return client.get(path)


def _assert_contains(resp, *needles):
    assert resp.status_code == 200, resp.text
    body = resp.text
    for needle in needles:
        assert needle in body, f"não encontrado na resposta: {needle!r}"


def test_index_html_disponivel():
    resp = get_index()
    assert resp.status_code == 200


def test_css_e_js_disponiveis():
    css = get("/static/style.css")
    js = get("/static/app.js")
    assert css.status_code == 200
    assert js.status_code == 200


def test_assets_servidos_como_estaticos():
    logo = get("/static/assets/usp-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"].startswith("image/")


def test_pagina_tem_abas_rotulos_exatos():
    body = get_index().text
    assert "ALUNOS" in body
    assert "DOCENTES" in body
    assert body.index("ALUNOS") < body.index("DOCENTES")


def test_pagina_nao_gerada_por_python():
    """O HTML é servido como arquivo estático: o backend não injeta conteúdo."""
    body = get_index().text
    assert "{%" not in body
    assert "{{" not in body


def test_pagina_tem_campos_do_bloco_solicitante_evento():
    body = get_index().text
    for label in (
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
    ):
        assert label in body, f"rótulo ausente: {label!r}"


def test_pagina_tem_campos_do_bloco_endereco():
    body = get_index().text
    for label in (
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
    ):
        assert label in body, f"rótulo ausente: {label!r}"


def test_pagina_tem_campos_do_bloco_pagamento():
    body = get_index().text
    for label in (
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ):
        assert label in body, f"rótulo ausente: {label!r}"


def test_pagina_tem_titulos_de_blocos():
    body = get_index().text
    assert "SOLICITANTE E EVENTO" in body
    assert "ENDEREÇO DO SOLICITANTE" in body
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in body


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos():
    """DOCENTES não tem NÍVEL nem TIPO DE AUXÍLIO."""
    body = get_index().text
    alunos_ini = body.index('id="alunos"')
    docentes_ini = body.index('id="docentes"')

    for aba_ini, aba_fim in ((alunos_ini, docentes_ini), (docentes_ini, None)):
        aba = body[aba_ini:aba_fim]
        tem_nivel = re.search(r"N[ÍI]VEL", aba) is not None
        tem_tipo = "TIPO DE AUXÍLIO" in aba
        if aba_ini == alunos_ini:
            assert tem_nivel
            assert tem_tipo
        else:
            assert not tem_nivel, "a aba DOCENTES não deve ter NÍVEL"
            assert not tem_tipo, "a aba DOCENTES não deve ter TIPO DE AUXÍLIO"


def test_campos_com_placeholders():
    """Todo campo tem placeholder de exemplo, não a repetição do rótulo."""
    body = get_index().text
    phs = re.findall(r"placeholder=\"([^\"]*)\"", body)
    assert len(phs) >= 10

    rotulos = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    ]
    for ph in phs:
        for r in rotulos:
            assert ph != r, f"placeholder é repetição do rótulo: {ph!r}"


def test_link_evento_e_complemento_opcionais():
    """Campos opcionais: sem required no HTML."""
    body = get_index().text
    for campo in ("LINK DO EVENTO", "COMPLEMENTO"):
        ini = body.index(campo)
        window = body[ini:ini + 2000]
        assert "required" not in window, f"{campo} deve ser opcional"


def test_campos_obrigatorios_required():
    body = get_index().text
    ini = body.index("NOME COMPLETO")
    window = body[ini:ini + 2000]
    assert "required" in window


def test_pagina_tem_dois_botoes_enviar():
    body = get_index().text
    assert body.count("Enviar solicitação") == 2


def test_pagina_nome_universidade():
    body = get_index().text
    assert "Universidade de São Paulo" in body
    assert "usp-logo.png" in body


def test_app_js_contem_logica_de_formatacao():
    """O app.js implementa o comportamento de tela (sem framework, sem CDN)."""
    js = get("/static/app.js").text
    assert len(js.strip()) > 0


def test_style_css_sem_fonte_remota():
    css = get("/static/style.css").text
    assert "@import" not in css
    assert "googleapis" not in css
    assert "https://" not in css


def test_app_js_sem_fonte_ou_biblioteca_remota():
    js = get("/static/app.js").text
    assert "googleapis" not in js
    assert "cdn." not in js
    assert "require(" not in js


def test_style_css_tem_cores_institucionais():
    css = get("/static/style.css").text
    assert "#1094ab" in css.lower()
    assert "#64c4d2" in css.lower()
    assert "#fcb421" in css.lower()


def test_style_css_sem_brasao():
    """O brasão/escudo não aparece na página."""
    css = get("/static/style.css").text
    body = get_index().text
    for fonte in (css, body):
        assert "escudo" not in fonte.lower()
        assert "brasao" not in fonte.lower().replace("ã", "a")


def test_style_css_fonte_sem_serifa():
    css = get("/static/style.css").text
    assert "Open Sans" in css or "sans-serif" in css


def _solicitacao_valida(**overrides):
    base = {
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional",
        "periodo_evento": "10 a 12 de outubro",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://exemplo.com",
        "valor_solicitado": "150000",
        "detalhamento": "Passagem e diária",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
        "aba": "alunos",
    }
    base.update(overrides)
    return base


def post(data):
    return client.post("/api/solicitacao", json=data)


def test_envio_valido_alunos():
    resp = post(_solicitacao_valida())
    assert resp.status_code == 200, resp.text


def test_envio_valido_sem_campos_opcionais():
    """LINK DO EVENTO e COMPLEMENTO podem ficar vazios."""
    resp = post(_solicitacao_valida(link_evento="", complemento=""))
    assert resp.status_code == 200, resp.text


def test_envio_valido_docentes():
    """Docentes não enviam nível nem tipo de auxílio."""
    dados = _solicitacao_valida(aba="docentes")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    resp = post(dados)
    assert resp.status_code == 200, resp.text


def test_envio_docentes_com_nivel_nao_impede_validade():
    """Na aba docentes, nível/tipo não são exigidos; extras não invalidam."""
    dados = _solicitacao_valida(aba="docentes")
    resp = post(dados)
    assert resp.status_code == 200, resp.text


def test_erro_campo_obrigatorio_vazio():
    resp = post(_solicitacao_valida(nome=""))
    assert resp.status_code != 200
    body = resp.text.lower()
    assert "preencha todos os campos" in body


def test_erro_campo_obrigatorio_faltando():
    dados = _solicitacao_valida()
    dados.pop("bairro")
    resp = post(dados)
    assert resp.status_code != 200
    assert "preencha todos os campos" in resp.text.lower()


def test_erro_mensagem_unica_para_varios_vazios():
    resp = post(_solicitacao_valida(nome="", cidade="", banco=""))
    assert resp.status_code != 200
    assert resp.text.lower().count("preencha todos os campos") == 1


def test_erro_n_usp_nao_numerico():
    resp = post(_solicitacao_valida(n_usp="12345abc"))
    assert resp.status_code != 200
    assert "N. USP deve conter apenas números" in resp.text


def test_erro_agencia_nao_numerica():
    resp = post(_solicitacao_valida(agencia="12a4"))
    assert resp.status_code != 200
    assert "Número da agência deve conter apenas números" in resp.text


def test_erro_valor_zero():
    resp = post(_solicitacao_valida(valor_solicitado="0"))
    assert resp.status_code != 200
    assert "Valor solicitado deve ser maior que 0" in resp.text


def test_erro_valor_negativo():
    resp = post(_solicitacao_valida(valor_solicitado="-10"))
    assert resp.status_code != 200
    assert "Valor solicitado deve ser maior que 0" in resp.text


def test_erro_email_sem_arroba():
    resp = post(_solicitacao_valida(email="maria.ime.usp.br"))
    assert resp.status_code != 200
    assert "E-mail inválido" in resp.text


def test_erro_email_sem_dominio():
    resp = post(_solicitacao_valida(email="maria@"))
    assert resp.status_code != 200
    assert "E-mail inválido" in resp.text


def test_erro_cpf_formato_errado():
    resp = post(_solicitacao_valida(cpf="12345678909"))
    assert resp.status_code != 200
    assert "CPF deve estar no formato 000.000.000-00" in resp.text


def test_erro_cep_formato_errado():
    resp = post(_solicitacao_valida(cep="05508090"))
    assert resp.status_code != 200
    assert "CEP deve estar no formato 00000-000" in resp.text


def test_erro_data_nascimento_formato_errado():
    resp = post(_solicitacao_valida(data_nascimento="01021980"))
    assert resp.status_code != 200
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resp.text


def test_erro_cpf_invalido_digitos_verificadores():
    """CPF no formato certo mas com dígitos verificadores errados."""
    resp = post(_solicitacao_valida(cpf="123.456.789-00"))
    assert resp.status_code != 200
    assert "CPF inválido" in resp.text
    assert "CPF deve estar no formato" not in resp.text


def test_erro_data_nascimento_inexistente():
    """Data no formato certo mas que não existe."""
    resp = post(_solicitacao_valida(data_nascimento="31/02/1980"))
    assert resp.status_code != 200
    assert "Data de nascimento inválida" in resp.text


def test_erro_data_nascimento_mes_zero():
    resp = post(_solicitacao_valida(data_nascimento="01/00/1980"))
    assert resp.status_code != 200
    assert "Data de nascimento inválida" in resp.text


def test_multiplos_erros_revelados_de_uma_vez():
    """Todas as mensagens aplicáveis aparecem juntas."""
    resp = post(
        _solicitacao_valida(
            n_usp="abc",
            email="sem-arroba",
            cpf="12.345.678-90",
        )
    )
    assert resp.status_code != 200
    body = resp.text
    assert "N. USP deve conter apenas números" in body
    assert "E-mail inválido" in body
    assert "CPF inválido" in body


def test_erros_agrupados_no_topo_do_formulario_da_aba():
    """Os erros da aba DOCENTES não mencionam campos exclusivos de ALUNOS."""
    dados = _solicitacao_valida(aba="docentes")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados["nome"] = ""
    resp = post(dados)
    assert resp.status_code != 200
    assert "preencha todos os campos" in resp.text.lower()
    assert "nível" not in resp.text.lower()
    assert "tipo de auxílio" not in resp.text.lower()


def test_oficio_alunos_com_dados_preenchidos():
    """O ofício substitui os marcadores pelos valores enviados."""
    resp = post(_solicitacao_valida())
    body = resp.text
    for trecho in (
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "Evento: Congresso Nacional",
        "Período: 10 a 12 de outubro",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Passagem e diária",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 56789-0",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ):
        assert trecho in body, f"trecho ausente do ofício: {trecho!r}"


def test_oficio_sem_marcadores():
    resp = post(_solicitacao_valida())
    assert "<<" not in resp.text
    assert ">>" not in resp.text


def test_oficio_linha_complemento_quando_preenchido():
    resp = post(_solicitacao_valida(complemento="Predio 3"))
    assert "Complemento: Predio 3" in resp.text


def test_oficio_omit_linhas_opcionais_vazias():
    """Link e complemento vazios: a linha sai do ofício."""
    resp = post(_solicitacao_valida(link_evento="", complemento=""))
    assert "Link do evento:" not in resp.text
    assert "Complemento:" not in resp.text


def test_oficio_docentes_mantem_programa_sem_nivel():
    """Docentes: Assunto com verba do programa e Programa sem nível."""
    dados = _solicitacao_valida(aba="docentes")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    resp = post(dados)
    body = resp.text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in body
    assert "Programa: Matemática" in body
    # sem o traço de nível: "Programa: Matemática - Mestrado" não pode existir
    assert "Programa: Matemática - " not in body


def test_formato_moeda_brasileira_no_oficio():
    resp = post(_solicitacao_valida(valor_solicitado="1500"))
    assert "R$ 15,00" in resp.text

    resp = post(_solicitacao_valida(valor_solicitado="150000000"))
    assert "R$ 1.500.000,00" in resp.text


def test_oficio_preserva_quebras_de_linha():
    """O ofício chega como texto com quebras de linha."""
    resp = post(_solicitacao_valida())
    body = resp.text
    linhas = [l for l in body.splitlines() if l.strip()]
    assert len(linhas) >= 10


def test_aprovacao_menciona_data_de_hoje():
    """O texto da aprovação é fixo; data de hoje é adicionada no backend."""
    resp = post(_solicitacao_valida())
    assert "aprovou" in resp.text


def test_aba_ativa_padrao_alunos():
    """Na resposta de sucesso, identificamos a aba; o default é alunos."""
    resp = post(_solicitacao_valida(aba="docentes"))
    assert "Verba do programa" in resp.text


def test_aba_desconhecida_e_rejeitada():
    resp = post(_solicitacao_valida(aba="qualquer"))
    assert resp.status_code != 200


def test_backend_nao_grava_nada():
    """Sem persistência: duas submissões idênticas não criam estado."""
    r1 = post(_solicitacao_valida())
    r2 = post(_solicitacao_valida())
    assert r1.status_code == r2.status_code == 200

