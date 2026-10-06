import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

CAMINHOS = [
    "/solicitacao",
    "/solicitar",
    "/solicitacoes",
    "/formulario",
    "/enviar",
    "/auxilio",
    "/api/solicitacao",
    "/api/solicitar",
    "/api/solicitacoes",
    "/api/formulario",
    "/api/enviar",
    "/api/auxilio",
    "/",
]

ALIASES = {
    "nome_completo": ["nome_completo", "nomeCompleto", "nome"],
    "n_usp": ["n_usp", "nusp", "numero_usp", "num_usp"],
    "programa": ["programa"],
    "nivel": ["nivel"],
    "tipo_auxilio": ["tipo_auxilio", "tipoAuxilio", "tipo_de_auxilio"],
    "email": ["email", "e_mail"],
    "evento": ["nome_evento", "nomeEvento", "evento", "nome_do_evento"],
    "periodo": ["periodo", "periodo_evento", "periodoEvento"],
    "cidade_evento": ["cidade_evento", "cidadeEvento", "cidade_do_evento"],
    "estado_evento": ["estado_evento", "estadoEvento", "uf_evento"],
    "pais_evento": ["pais_evento", "paisEvento", "pais"],
    "link": ["link", "link_evento", "linkEvento", "link_do_evento"],
    "valor": ["valor", "valor_solicitado", "valorSolicitado"],
    "detalhamento": ["detalhamento", "detalhamento_pedido", "detalhamentoPedido"],
    "apresentacao": ["apresentacao", "tipo_apresentacao", "apresentacao_trabalho"],
    "data_nascimento": ["data_nascimento", "dataNascimento", "nascimento"],
    "logradouro": ["logradouro", "rua", "endereco"],
    "numero": ["numero", "num", "numero_endereco"],
    "complemento": ["complemento"],
    "bairro": ["bairro"],
    "cep": ["cep"],
    "cidade": ["cidade"],
    "estado": ["estado", "uf"],
    "cpf": ["cpf"],
    "rg": ["rg", "rg_rnm", "rnm"],
    "banco": ["banco", "nome_banco", "nomeBanco"],
    "agencia": ["agencia", "numero_agencia", "num_agencia"],
    "conta": ["conta", "numero_conta", "num_conta"],
}

BASE_ALUNOS = {
    "nome_completo": "Fulano de Tal",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "fulano@usp.br",
    "evento": "Congresso de Testes",
    "periodo": "10 a 15 de março de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link": "https://exemplo.com/evento",
    "valor": "150000",
    "detalhamento": "Preciso do auxílio para custear passagens e hospedagem.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua das Flores",
    "numero": "100",
    "complemento": "Bloco A",
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

BASE_DOCENTES = {
    chave: valor
    for chave, valor in BASE_ALUNOS.items()
    if chave not in ("nivel", "tipo_auxilio")
}

ROTULOS = [
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


def montar(base, troca=None):
    valores = dict(base)
    if troca:
        valores.update(troca)
    dados = {}
    for logico, valor in valores.items():
        for chave in ALIASES[logico]:
            dados[chave] = valor
    return dados


def dados_alunos(**troca):
    return montar(BASE_ALUNOS, troca)


def dados_docentes(**troca):
    return montar(BASE_DOCENTES, troca)


def respostas(dados):
    saida = []
    for caminho in CAMINHOS:
        for corpo in ({"data": dados}, {"json": dados}):
            try:
                resposta = client.post(caminho, **corpo)
            except Exception:
                continue
            saida.append(resposta.text or "")
    return saida


def textos(dados):
    return "\n".join(respostas(dados))


def pagina():
    for caminho in ("/", "/index.html", "/static/index.html"):
        resposta = client.get(caminho)
        if resposta.status_code == 200 and "<" in (resposta.text or ""):
            return resposta.text
    return ""


def estatico(nome):
    for caminho in (f"/{nome}", f"/static/{nome}"):
        resposta = client.get(caminho)
        if resposta.status_code == 200 and resposta.text:
            return resposta.text
    return ""


def test_pagina_inicial_servida():
    assert "<html" in pagina().lower()


def test_pagina_tem_as_duas_abas_na_ordem():
    html = pagina()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_pagina_tem_os_titulos_dos_blocos():
    html = pagina()
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in html


def test_pagina_tem_o_cabecalho_institucional():
    html = pagina()
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_pagina_tem_os_rotulos_dos_campos():
    conteudo = pagina() + estatico("app.js") + estatico("style.css")
    for rotulo in ROTULOS:
        assert rotulo in conteudo, f"faltou o rótulo: {rotulo}"


def test_pagina_tem_as_opcoes_de_selecao():
    conteudo = pagina() + estatico("app.js")
    for opcao in (
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in conteudo, f"faltou a opção: {opcao}"


def test_pagina_tem_o_botao_de_envio():
    assert "Enviar solicitação" in pagina()


def test_arquivos_estaticos_servidos():
    assert estatico("style.css"), "style.css não foi servido"
    assert estatico("app.js"), "app.js não foi servido"


def test_logo_da_usp_servido():
    for caminho in (
        "/assets/usp-logo.png",
        "/static/assets/usp-logo.png",
        "/usp-logo.png",
    ):
        if client.get(caminho).status_code == 200:
            return
    raise AssertionError("assets/usp-logo.png não foi servido")


def test_css_tem_as_cores_da_universidade():
    css = estatico("style.css").lower()
    assert "#1094ab" in css
    assert "sans-serif" in css


def test_sem_cdn_ou_fonte_remota():
    for conteudo in (pagina(), estatico("style.css")):
        assert "cdn." not in conteudo.lower()
        assert "googleapis" not in conteudo.lower()
        assert "unpkg" not in conteudo.lower()


def test_envio_valido_gera_oficio_para_alunos():
    alvos = [
        t
        for t in respostas(dados_alunos())
        if "Interessada(o): Fulano de Tal - 12345678" in t
    ]
    assert alvos, "o ofício do aluno não foi gerado"
    oficio = alvos[0]
    for trecho in (
        "Interessada(o): Fulano de Tal - 12345678",
        "E-mail: fulano@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Mestrado",
        "A CCP-Ciência da Computação aprovou na data de hoje",
        "Dados do evento",
        "Evento: Congresso de Testes",
        "Período: 10 a 15 de março de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com/evento",
        "Apresentação de trabalho: Pôster",
        "Detalhamento: Preciso do auxílio para custear passagens e hospedagem.",
        "Endereço da(o) interessada(o)",
        "Rua das Flores, 100",
        "Complemento: Bloco A",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 56789-0",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ):
        assert trecho in oficio, f"faltou no ofício: {trecho}"
    assert re.search(r"Valor solicitado:.*1\.?500", oficio), "valor no ofício"
    assert "<<" not in oficio


def test_envio_valido_gera_oficio_para_docentes():
    alvos = [
        t
        for t in respostas(dados_docentes())
        if "Interessada(o): Fulano de Tal - 12345678" in t
    ]
    assert alvos, "o ofício do docente não foi gerado"
    oficio = alvos[0]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Programa: Ciência da Computação - Mestrado" not in oficio
    assert "<<" not in oficio


def test_link_e_complemento_vazios_saem_do_oficio():
    dados = dados_alunos(link="", complemento="")
    alvos = [
        t for t in respostas(dados) if "Interessada(o): Fulano de Tal - 12345678" in t
    ]
    assert alvos, "o ofício não foi gerado"
    oficio = alvos[0]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_campos_obrigatorios_vazios():
    vazios = {chave: "" for chave in BASE_ALUNOS}
    listas = respostas(dados_alunos(**vazios))
    assert any("Preencha todos os campos" in t for t in listas)
    for t in listas:
        if "Preencha todos os campos" in t:
            assert t.count("Preencha todos os campos") == 1
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_n_usp_apenas_digitos():
    listas = respostas(dados_alunos(n_usp="12345a"))
    assert any("N. USP deve conter apenas números" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_agencia_apenas_digitos():
    listas = respostas(dados_alunos(agencia="12-34"))
    assert any(
        "Número da agência deve conter apenas números" in t for t in listas
    )
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_valor_maior_que_zero():
    listas = respostas(dados_alunos(valor="0"))
    assert any("Valor solicitado deve ser maior que 0" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_email_invalido():
    listas = respostas(dados_alunos(email="fulano"))
    assert any("E-mail inválido" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_cpf_fora_do_formato():
    listas = respostas(dados_alunos(cpf="12345678909"))
    assert any("CPF deve estar no formato 000.000.000-00" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_cep_fora_do_formato():
    listas = respostas(dados_alunos(cep="05508090"))
    assert any("CEP deve estar no formato 00000-000" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_data_fora_do_formato():
    listas = respostas(dados_alunos(data_nascimento="01021980"))
    assert any(
        "Data de nascimento deve estar no formato dd/mm/aaaa" in t for t in listas
    )
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_cpf_com_digitos_verificadores_errados():
    listas = respostas(dados_alunos(cpf="123.456.789-00"))
    assert any("CPF inválido" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_data_inexistente():
    listas = respostas(dados_alunos(data_nascimento="31/02/1980"))
    assert any("Data de nascimento inválida" in t for t in listas)
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)


def test_mostra_todos_os_erros_de_uma_vez():
    dados = dados_alunos(
        n_usp="12a",
        agencia="1-2",
        valor="0",
        email="fulano",
        cpf="12345678909",
        cep="05508090",
        data_nascimento="01021980",
    )
    listas = respostas(dados)
    juntas = "\n".join(listas)
    for mensagem in (
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert mensagem in juntas, f"faltou a mensagem: {mensagem}"
    assert not any("Interessada(o): Fulano de Tal" in t for t in listas)
