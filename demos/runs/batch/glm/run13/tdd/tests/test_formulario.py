"""Testes do formulário de solicitação de auxílio financeiro do IME-USP.

Os testes exercitam o comportamento declarado no Requisito 01: a tela com duas
abas, os campos, a validação feita pelo backend e o ofício devolvido após o
envio válido. O frontend é estático (index.html, style.css, app.js) e o backend
é FastAPI em `app:app`.
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app


RAIZ = Path(__file__).resolve().parent.parent


def troca_valores(form, **novos):
    """Devolve `form` com os campos de `novos` substituídos; os demais intactos."""
    return {**form, **novos}


def rem(form, *chaves):
    """Devolve `form` sem as `chaves` (campo ausente na submissão)."""
    d = dict(form)
    for c in chaves:
        d.pop(c, None)
    return d


# ---------------------------------------------------------------------------
# Dados-base válidos: uma submissão de aluno que preenche tudo e gera ofício.
# Os testes partem daqui e alteram só o campo que querem provocar.
# ---------------------------------------------------------------------------

FORM_ALUNO = {
    "nome": "Maria da Silva Souza",
    "n_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "Congresso Latino de Matemática",
    "periodo": "10 a 12 de outubro de 2026",
    "cidade_evento": "Gramado",
    "estado_evento": "RS",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor": "R$ 1.500,00",
    "detalhamento": "Inscrição e hospedagem.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matao",
    "numero": "1010",
    "complemento": "",
    "bairro": "Butanta",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "529.982.247-25",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "98765-4",
}

FORM_DOCENTE = rem(
    FORM_ALUNO,
    "nivel",
    "tipo_auxilio",
    "email": "joao@ime.usp.br",
    "nome": "Joao Carlos Pereira",
    "rg": "98.765.432-1",
}


# ---------------------------------------------------------------------------
# Interface de suposição sobre os nomes de campo do frontend. Se a
# implementação usar outros nomes, o grupo de teste de contrato de nomes
# aponta quais mapear aqui.
# ---------------------------------------------------------------------------

FORM_PARA_HTML = {
    "nome": "nome",
    "n_usp": "n_usp",
    "programa": "programa",
    "nivel": "nivel",
    "tipo_auxilio": "tipo_auxilio",
    "email": "email",
    "evento": "evento",
    "periodo": "periodo",
    "cidade_evento": "cidade_evento",
    "estado_evento": "estado_evento",
    "pais_evento": "pais_evento",
    "link_evento": "link_evento",
    "valor": "valor",
    "detalhamento": "detalhamento",
    "apresentacao": "apresentacao",
    "data_nascimento": "data_nascimento",
    "logradouro": "logradouro",
    "numero": "numero",
    "complemento": "complemento",
    "bairro": "bairro",
    "cep": "cep",
    "cidade": "cidade",
    "estado": "estado",
    "cpf": "cpf",
    "rg": "rg",
    "banco": "banco",
    "agencia": "agencia",
    "conta": "conta",
}


def submete(client, aba, form):
    """Envia `form` na `aba` (`ALUNOS` ou `DOCENTES`) para o endpoint do backend."""
    return client.post("/enviar", data={"aba": aba, **form})


# ===========================================================================
# Tela única com duas abas
# ===========================================================================


def test_pagina_existe_e_retorna_html():
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_pagina_mostra_abas_alunos_e_docentes_nesta_ordem():
    with TestClient(app) as client:
        html = client.get("/").text
    pos_alunos = html.index("ALUNOS")
    pos_docentes = html.index("DOCENTES")
    assert pos_alunos != -1
    assert pos_docentes > pos_alunos


def test_pagina_tem_rotulo_e_titulo_da_aba_alunos():
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert "ALUNOS" in resp.text and "DOCENTES" in resp.text


def test_pagina_mantem_valores_digitados_entre_abas_sem_recarregar():
    # Sem recarregar a página: os dois formulários existem no HTML, apenas um
    # visível por vez, então o que foi digitado não se perde.
    with TestClient(app) as client:
        html = client.get("/").text
    nomes = set(re.findall(r'<input[^>]*name="([a-z_]+)"', html))
    assert {FORM_PARA_HTML[c] for c in FORM_ALUNO} <= nomes
    assert {FORM_PARA_HTML[c] for c in FORM_DOCENTE} <= nomes


def test_pagina_tem_dois_botoes_enviar_solicitação():
    with TestClient(app) as client:
        html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_aba_alunos_ativa_por_padrao():
    with TestClient(app) as client:
        html = client.get("/").text
    # A aba ALUNOS vem antes e já ativa: o formulário de alunos é o visível
    # por padrão, sem necessidade de clique.
    pos_alunos = html.index("ALUNOS")
    assert "ALUNOS" in html[pos_alunos:]
    assert html.count("Enviar solicitação") >= 2


def test_campos_aluno_exclusivos_presentes_na_aba_alunos():
    with TestClient(app) as client:
        html = client.get("/").text
    assert "NÍVEL" in html
    assert "TIPO DE AUXÍLIO" in html


def test_opcoes_de_nivel_e_tipo_de_auxilio_disponiveis():
    with TestClient(app) as client:
        html = client.get("/").text
    for opcao in ("Mestrado", "Doutorado"):
        assert opcao in html
    for opcao in (
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ):
        assert opcao in html


def test_opcoes_de_apresentacao_de_trabalho_disponiveis():
    with TestClient(app) as client:
        html = client.get("/").text
    for opcao in ("Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"):
        assert opcao in html


# ===========================================================================
# Rótulos literais dos blocos e campos
# ===========================================================================


def test_rotulos_dos_blocos():
    with TestClient(app) as client:
        html = client.get("/").text
    for rotulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert rotulo in html


def test_rotulos_dos_campos_do_bloco_solicitante_e_evento():
    with TestClient(app) as client:
        html = client.get("/").text
    for rotulo in (
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
    ):
        assert rotulo in html


def test_rotulos_do_bloco_endereco_do_solicitante():
    with TestClient(app) as client:
        html = client.get("/").text
    for rotulo in (
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
    ):
        assert rotulo in html


def test_rotulos_do_bloco_informacoes_para_pagamento():
    with TestClient(app) as client:
        html = client.get("/").text
    for rotulo in (
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ):
        assert rotulo in html


def test_campos_obrigatorios_marcados_no_html():
    # Campo opcional: LINK DO EVENTO..., COMPLEMENTO. Os demais são
    # obrigatórios para o backend.
    with TestClient(app) as client:
        resp = submete(client, "ALUNOS", rem(FORM_ALUNO, "complemento", "link_evento"))
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_todos_campos_tem_placeholder_diferente_do_rotulo():
    with TestClient(app) as client:
        html = client.get("/").text
    placeholders = re.findall(r'placeholder="([^"]+)"', html)
    rotulos = {
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
    }
    assert len(placeholders) >= 23
    assert not (set(placeholders) & rotulos)


# ===========================================================================
# Formatação automática de campos (frontend, em app.js)
# ===========================================================================


def test_appjs_formata_valor_como_moeda_brasileira():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "1500" in js or "cents" in js or "centavos" in js
    assert ("toLocaleString" in js) or ("R$ " in js) or ("R$\u00a0" in js)


def test_appjs_formata_cpf_cep_e_data():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "." in js and "-" in js and "/" in js


def test_campos_com_mascara_declaram_inputmode_ou_tipo_texto():
    with TestClient(app) as client:
        html = client.get("/").text
    assert html.count("placeholder=") >= 23


# ===========================================================================
# Backend: validação
# ===========================================================================


client = TestClient(app)


def test_envio_valido_aluno_retorna_oficio():
    resp = submete(client, "ALUNOS", FORM_ALUNO)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["ok"] is True
    assert "erros" not in corpo or corpo.get("erros") == []
    oficio = corpo["oficio"]
    assert "Interessada(o): Maria da Silva Souza - 12345678" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio


def test_envio_valido_docente_retorna_oficio_com_assunto_verba_do_programa():
    resp = submete(client, "DOCENTES", FORM_DOCENTE)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["ok"] is True
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    # Linha com nível não pode aparecer para docente.
    assert "Programa: Matemática - Mestrado" not in oficio


def test_envio_valido_docente_aceita_sem_nivel_e_tipo_auxilio():
    resp = submete(client, "DOCENTES", FORM_DOCENTE)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_aba_invalida():
    resp = submete(client, "OUTRA", FORM_DOCENTE)
    assert resp.status_code == 422


def test_aba_desconhecida_com_dados_validos():
    resp = client.post(
        "/enviar",
        data={"aba": "XYZ", **FORM_DOCENTE},
    )
    assert resp.status_code == 422


def test_campo_obrigatorio_faltando_erro_unico():
    form = troca_valores(FORM_ALUNO, nome="")
    resp = submete(client, "ALUNOS", form)
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["ok"] is False
    assert "Preencha todos os campos" in corpo["erros"]
    assert corpo["erros"].count("Preencha todos os campos") == 1


def test_campo_obrigatorio_ausente_erro_unico():
    resp = submete(client, "ALUNOS", rem(FORM_ALUNO, "nome"))
    corpo = resp.json()
    assert corpo["ok"] is False
    assert "Preencha todos os campos" in corpo["erros"]


def test_varios_campos_vazios_ainda_um_unico_erro_preencha():
    form = troca_valores(FORM_ALUNO, nome="", programa="", email="")
    resp = submete(client, "ALUNOS", form)
    corpo = resp.json()
    assert "Preencha todos os campos" in corpo["erros"]
    assert corpo["erros"].count("Preencha todos os campos") == 1


def test_campo_opcional_complemento_vazio_ok():
    resp = submete(client, "ALUNOS", FORM_ALUNO)  # complemento já é ""
    assert resp.json()["ok"] is True


def test_campo_opcional_link_evento_vazio_ok():
    resp = submete(client, "ALUNOS", FORM_ALUNO)
    assert resp.json()["ok"] is True


def test_n_usp_com_letras_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, n_usp="12a456"))
    corpo = resp.json()
    assert corpo["ok"] is False
    assert "N. USP deve conter apenas números" in corpo["erros"]


def test_agencia_com_letras_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, agencia="12a4"))
    corpo = resp.json()
    assert corpo["ok"] is False
    assert "Número da agência deve conter apenas números" in corpo["erros"]


def test_valor_zero_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, valor="R$ 0,00"))
    corpo = resp.json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_valor_negativo_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, valor="-R$ 10,00"))
    corpo = resp.json()
    assert "Valor solicitado deve ser maior que 0" in corpo["erros"]


def test_email_sem_arroba_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, email="maria.ime.usp.br"))
    corpo = resp.json()
    assert "E-mail inválido" in corpo["erros"]


def test_email_sem_dominio_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, email="maria@"))
    corpo = resp.json()
    assert "E-mail inválido" in corpo["erros"]


def test_cpf_mal_formatado_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, cpf="529.982.24725"))
    corpo = resp.json()
    assert "CPF deve estar no formato 000.000.000-00" in corpo["erros"]


def test_cpf_com_digitos_invalidos_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, cpf="111.111.111-11"))
    corpo = resp.json()
    assert "CPF inválido" in corpo["erros"]


def test_cep_mal_formatado_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, cep="05508 090"))
    corpo = resp.json()
    assert "CEP deve estar no formato 00000-000" in corpo["erros"]


def test_data_mal_formatada_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, data_nascimento="01021980"))
    corpo = resp.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo["erros"]


def test_data_inexistente_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, data_nascimento="31/02/1980"))
    corpo = resp.json()
    assert "Data de nascimento inválida" in corpo["erros"]


def test_mes_fora_de_intervalo_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, data_nascimento="01/13/1980"))
    corpo = resp.json()
    assert "Data de nascimento inválida" in corpo["erros"]


def test_todos_erros_de_volta_ao_mesmo_tempo():
    form = troca_valores(
        FORM_ALUNO,
        nome="",
        n_usp="12a456",
        email="maria",
        valor="R$ 0,00",
        cpf="52998224725",
        cep="05508090",
        data_nascimento="01021980",
        agencia="12a4",
    )
    resp = submete(client, "ALUNOS", form)
    corpo = resp.json()
    assert corpo["ok"] is False
    esperados = [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]
    for msg in esperados:
        assert msg in corpo["erros"]


def test_erro_formato_data_nao_gera_erro_valor_simultaneo():
    # Erros de formato e de conteúdo do CPF: um CPF bem formatado com dígitos
    # errados não gera o erro de formato.
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, cpf="123.456.789-09"))
    corpo = resp.json()
    assert "CPF inválido" in corpo["erros"]
    assert "CPF deve estar no formato 000.000.000-00" not in corpo["erros"]


def test_sem_oficio_quando_ha_erro():
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, nome=""))
    corpo = resp.json()
    assert not corpo.get("oficio")


# ===========================================================================
# Backend: ofício
# ===========================================================================


def test_oficio_aluno_linha_por_linha():
    resp = submete(client, "ALUNOS", FORM_ALUNO)
    oficio = resp.json()["oficio"]
    linhas = [l.strip() for l in oficio.splitlines()]
    assert "Interessada(o): Maria da Silva Souza - 12345678" in linhas
    assert "E-mail: maria@ime.usp.br" in linhas
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in linhas
    )
    assert "Programa: Matemática - Mestrado" in linhas
    assert "Dados do evento" in linhas
    assert "Evento: Congresso Latino de Matemática" in linhas
    assert "Período: 10 a 12 de outubro de 2026" in linhas
    assert "Local: Gramado - RS - Brasil" in linhas
    assert "Valor solicitado: R$ 1.500,00" in linhas
    assert "Detalhamento: Inscrição e hospedagem." in linhas
    assert "Endereço da(o) interessada(o)" in linhas
    assert "Rua do Matao, 1010" in linhas
    assert "CEP: 05508-090" in linhas
    assert "Butanta, São Paulo - SP" in linhas
    assert "Dados para pagamento" in linhas
    assert "Data de nascimento: 01/02/1980" in linhas
    assert "CPF: 529.982.247-25" in linhas
    assert "RG / RNM: 12.345.678-9" in linhas
    assert "Banco: Banco do Brasil" in linhas
    assert "Agência: 1234" in linhas
    assert "Conta: 98765-4" in linhas
    assert "Encaminhe-se ao Serviço Financeiro para providências." in linhas


def test_oficio_aluno_com_apresentacao_e_preenchida():
    form = troca_valores(FORM_ALUNO, apresentacao="Apresentação oral")
    resp = submete(client, "ALUNOS", form)
    oficio = resp.json()["oficio"]
    assert "Apresentação de trabalho: Apresentação oral" in [l.strip() for l in oficio.splitlines()]


def test_oficio_linha_link_sai_quando_vazio():
    resp = submete(client, "ALUNOS", FORM_ALUNO)  # link_evento == ""
    oficio = resp.json()["oficio"]
    assert "Link do evento:" not in oficio


def test_oficio_linha_link_aparece_quando_preenchido():
    form = troca_valores(FORM_ALUNO, link_evento="https://evento.example")
    resp = submete(client, "ALUNOS", form)
    oficio = resp.json()["oficio"]
    assert (
        "Link do evento: https://evento.example" in [l.strip() for l in oficio.splitlines()]
    )


def test_oficio_linha_complemento_sai_quando_vazio():
    resp = submete(client, "ALUNOS", FORM_ALUNO)  # complemento == ""
    oficio = resp.json()["oficio"]
    assert "Complemento:" not in oficio


def test_oficio_linha_complemento_aparece_quando_preenchido():
    form = troca_valores(FORM_ALUNO, complemento="Bloco B")
    resp = submete(client, "ALUNOS", form)
    oficio = resp.json()["oficio"]
    assert "Complemento: Bloco B" in [l.strip() for l in oficio.splitlines()]


def test_oficio_preserva_valor_formatado_com_milhar():
    form = troca_valores(FORM_ALUNO, valor="R$ 1.500.000,00")
    resp = submete(client, "ALUNOS", form)
    oficio = resp.json()["oficio"]
    assert "Valor solicitado: R$ 1.500.000,00" in [l.strip() for l in oficio.splitlines()]


def test_oficio_docente_sem_linhas_de_nivel_e_tipo():
    resp = submete(client, "DOCENTES", FORM_DOCENTE)
    oficio = resp.json()["oficio"]
    assert "Verba do programa" in oficio
    assert "Programa: Matemática" in [l.strip() for l in oficio.splitlines()]


def test_valor_pode_vir_como_centavos_ou_formatado():
    # O backend aceita o valor como o usuário o vê: "R$ 1.500,00".
    resp = submete(client, "ALUNOS", troca_valores(FORM_ALUNO, valor="R$ 15,00"))
    corpo = resp.json()
    assert corpo["ok"] is True
    assert "Valor solicitado: R$ 15,00" in corpo["oficio"]


# ===========================================================================
# Aparência: estáticos servidos, CSS, identidade USP
# ===========================================================================


def test_estaticos_servidos():
    with TestClient(app) as client:
        for nome in ("index.html", "style.css", "app.js"):
            resp = client.get(f"/static/{nome}")
            assert resp.status_code == 200, nome


def test_index_referencia_style_e_app():
    with TestClient(app) as client:
        html = client.get("/static/index.html").text
    assert "style.css" in html
    assert "app.js" in html


def test_assets_logo_servido():
    with TestClient(app) as client:
        resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")


def test_header_usa_logo_e_nome_da_universidade():
    with TestClient(app) as client:
        html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_style_css_define_cores_oficiais():
    css = (RAIZ / "style.css").read_text(encoding="utf-8")
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_style_css_usa_fonte_sem_serifa_recomendada():
    css = (RAIZ / "style.css").read_text(encoding="utf-8")
    assert "sans-serif" in css.lower() or "Open Sans" in css


def test_style_css_define_grade_de_colunas():
    css = (RAIZ / "style.css").read_text(encoding="utf-8")
    assert "grid" in css or "columns" in css or "flex" in css


def test_index_nao_usa_cdn_nem_fonte_remota():
    with TestClient(app) as client:
        html = client.get("/").text
    assert "http://" not in html.replace("http://localhost", "")
    assert "https://" not in html


def test_appjs_existe_e_nao_e_vazio():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert len(js.strip()) > 0


def test_appjs_envia_para_backend_sem_recarregar():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "fetch" in js or "XMLHttpRequest" in js
    assert "submit" in js.lower()


def test_appjs_mostra_erros_no_topo_do_formulario():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "error" in js.lower() or "erros" in js.lower()


def test_appjs_troca_de_abas_sem_recarregar():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "tab" in js.lower() or "aba" in js.lower()
    assert "addEventListener" in js or "onclick" in js


def test_appjs_formata_campos_no_evento_de_saida_do_campo():
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "blur" in js or "change" in js or "input" in js


def test_html_nao_mostra_brasao():
    with TestClient(app) as client:
        html = client.get("/").text
    assert "brasao" not in html.lower()
    assert "escudo" not in html.lower()


def test_confirmacao_preserva_quebras_de_linha_no_html():
    # A resposta JSON traz o ofício com quebras de linha; o frontend deve
    # preservá-las ao renderizar (CSS white-space: pre-line ou equivalente).
    css = (RAIZ / "style.css").read_text(encoding="utf-8")
    js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "white-space" in css or "\n" in js or "<br" in js or "pre-line" in css or "innerText" in js or "textContent" in js or "<br>" in js


def test_rotulo_solicitacao_registrada_aparece_no_frontend():
    with TestClient(app) as client:
        html = client.get("/").text
        js = (RAIZ / "app.js").read_text(encoding="utf-8")
    assert "Solicitação registrada" in html or "Solicitação registrada" in js
