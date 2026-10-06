"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import app

RAIZ = Path(__file__).resolve().parents[1]

HTML = (RAIZ / "index.html").read_text(encoding="utf-8")
CSS = (RAIZ / "style.css").read_text(encoding="utf-8")
JS = (RAIZ / "app.js").read_text(encoding="utf-8")

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

VALORES = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria Silva Santos",
    "N. USP": "12345678",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria.santos@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de Computação",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/10/2024 a 12/10/2024",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "Campinas",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.exemplo.br",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Passagens e hospedagem.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Apresentação oral",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Bloco B",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "12345-6",
}


def _tela():
    return HTML + "\n" + JS


def test_pagina_inicial_servida():
    cliente = TestClient(app)
    respostas = [cliente.get(caminho) for caminho in ("/", "/index.html")]
    assert any(
        resposta.status_code == 200 and "Universidade de São Paulo" in resposta.text
        for resposta in respostas
    )


def test_cabecalho_institucional():
    assert "assets/usp-logo.png" in HTML
    assert "Universidade de São Paulo" in HTML


def test_sem_brasao():
    minusculo = HTML.lower()
    assert "brasao" not in minusculo
    assert "brasão" not in minusculo
    assert "escudo" not in minusculo


def test_abas_alunos_e_docentes_na_ordem():
    tela = _tela()
    assert "ALUNOS" in tela
    assert "DOCENTES" in tela
    assert tela.index("ALUNOS") < tela.index("DOCENTES")


def test_aba_alunos_ativa_ao_abrir():
    posicao = HTML.index("ALUNOS")
    trecho = HTML[max(0, posicao - 300):posicao + 300]
    assert any(
        marca in trecho
        for marca in ("active", "ativa", "selected", 'aria-selected="true"')
    )


def test_titulos_dos_blocos():
    tela = _tela()
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in tela, titulo


def test_rotulos_dos_campos():
    tela = _tela()
    for rotulo in ROTULOS:
        assert rotulo in tela, rotulo


def test_botao_enviar_em_cada_aba():
    assert HTML.count("Enviar solicitação") >= 2


def test_nivel_e_tipo_de_auxilio_apenas_na_aba_alunos():
    assert HTML.count("NÍVEL") == 1
    assert HTML.count("TIPO DE AUXÍLIO") == 1


def test_placeholders_com_exemplos():
    for tag in re.findall(r"<(?:input|textarea)\b[^>]*>", HTML):
        if re.search(r'type="(?:hidden|submit|button|radio|checkbox|reset)"', tag):
            continue
        achado = re.search(r'placeholder="([^"]*)"', tag)
        assert achado is not None, tag
        exemplo = achado.group(1).strip()
        assert exemplo, tag
        assert exemplo not in ROTULOS, tag


def test_cores_da_universidade():
    minusculo = CSS.lower()
    assert "#1094ab" in minusculo
    assert "#64c4d2" in minusculo
    assert "#fcb421" in minusculo


def test_fonte_sem_serifa():
    minusculo = CSS.lower()
    assert "open sans" in minusculo or "sans-serif" in minusculo


def test_layout_em_colunas():
    em_colunas = re.search(r"grid-template-columns\s*:[^;]*\S\s+\S", CSS)
    em_linha = re.search(r"display\s*:\s*flex", CSS) and re.search(r"flex-wrap\s*:", CSS)
    assert em_colunas or em_linha


def test_sem_recursos_da_rede():
    for conteudo in (HTML, CSS, JS):
        assert "fonts.googleapis.com" not in conteudo
        assert "@import" not in conteudo
        for atributo in ('src="http', "src='http", 'href="http', "href='http", "url(http"):
            assert atributo not in conteudo


def _campo(rotulo):
    exato = re.search(r">\s*" + re.escape(rotulo) + r"\s*<", HTML)
    inicio = exato.start() if exato else HTML.find(rotulo)
    assert inicio != -1, rotulo
    nome = re.search(r'name="([^"]+)"', HTML[inicio:inicio + 1000])
    assert nome is not None, rotulo
    return nome.group(1)


def _discriminador_da_aba_alunos():
    dados = {}
    for tag in re.findall(r"<input\b[^>]*>", HTML):
        if 'type="hidden"' not in tag:
            continue
        nome = re.search(r'name="([^"]+)"', tag)
        valor = re.search(r'value="([^"]*)"', tag)
        if nome and valor and "aluno" in valor.group(1).lower():
            dados[nome.group(1)] = valor.group(1)
    return dados


def _payload(trocas=None):
    dados = dict(_discriminador_da_aba_alunos())
    dados.update({_campo(rotulo): valor for rotulo, valor in VALORES.items()})
    dados.update({_campo(rotulo): valor for rotulo, valor in (trocas or {}).items()})
    return dados


MARCADORES = (
    "Preencha todos os campos",
    "N. USP deve conter apenas números",
    "E-mail inválido",
    "Interessada(o):",
)


def _enviar(payload):
    cliente = TestClient(app)
    caminhos = [
        rota.path
        for rota in app.routes
        if "POST" in (getattr(rota, "methods", None) or set())
    ]
    ultima = None
    for caminho in caminhos:
        for envio in ({"json": payload}, {"data": payload}):
            resposta = cliente.post(caminho, **envio)
            ultima = resposta
            if resposta.status_code < 400:
                return resposta
            if any(marcador in resposta.text for marcador in MARCADORES):
                return resposta
    return ultima


def test_envio_valido_gera_oficio():
    texto = _enviar(_payload()).text
    assert "Interessada(o): Maria Silva Santos - 12345678" in texto
    assert "E-mail: maria.santos@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "A CCP-Ciência da Computação aprovou na data de hoje" in texto
    assert "Dados do evento" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Período: 10/10/2024 a 12/10/2024" in texto
    assert "Local: Campinas - SP - Brasil" in texto
    assert "Link do evento: https://evento.exemplo.br" in texto
    assert "Apresentação de trabalho: Apresentação oral" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagens e hospedagem." in texto
    assert "Rua do Matão, 1010" in texto
    assert "Complemento: Bloco B" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
    assert "Preencha todos os campos" not in texto


def test_linhas_opcionais_vazias_somem_do_oficio():
    texto = _enviar(
        _payload(
            {
                "LINK DO EVENTO, EXAME OU DEFESA": "",
                "COMPLEMENTO": "",
            }
        )
    ).text
    assert "Interessada(o): Maria Silva Santos - 12345678" in texto
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_campo_obrigatorio_vazio():
    texto = _enviar({}).text
    assert "Preencha todos os campos" in texto
    assert texto.count("Preencha todos os campos") == 1
    assert "Interessada(o):" not in texto


def test_n_usp_apenas_numeros():
    texto = _enviar(_payload({"N. USP": "12a34"})).text
    assert "N. USP deve conter apenas números" in texto
    assert "Interessada(o):" not in texto


def test_agencia_apenas_numeros():
    texto = _enviar(_payload({"NÚMERO DA AGÊNCIA": "12a4"})).text
    assert "Número da agência deve conter apenas números" in texto


def test_valor_solicitado_maior_que_zero():
    texto = _enviar(_payload({"VALOR SOLICITADO (R$)": "0"})).text
    assert "Valor solicitado deve ser maior que 0" in texto


def test_email_invalido():
    texto = _enviar(_payload({"E-MAIL": "maria.ime.usp.br"})).text
    assert "E-mail inválido" in texto


def test_cpf_fora_do_formato():
    texto = _enviar(_payload({"CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909"})).text
    assert "CPF deve estar no formato 000.000.000-00" in texto


def test_cpf_invalido():
    texto = _enviar(_payload({"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})).text
    assert "CPF inválido" in texto


def test_cep_fora_do_formato():
    texto = _enviar(_payload({"CEP": "12345"})).text
    assert "CEP deve estar no formato 00000-000" in texto


def test_data_de_nascimento_fora_do_formato():
    texto = _enviar(_payload({"DATA DE NASCIMENTO": "01-02-1980"})).text
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto


def test_data_de_nascimento_inexistente():
    texto = _enviar(_payload({"DATA DE NASCIMENTO": "31/02/1980"})).text
    assert "Data de nascimento inválida" in texto


def test_varias_mensagens_de_erro_juntas():
    texto = _enviar(
        _payload(
            {
                "N. USP": "12a",
                "E-MAIL": "sem-arroba",
                "VALOR SOLICITADO (R$)": "0",
            }
        )
    ).text
    assert "N. USP deve conter apenas números" in texto
    assert "E-mail inválido" in texto
    assert "Valor solicitado deve ser maior que 0" in texto
    assert "Preencha todos os campos" not in texto
    assert "Interessada(o):" not in texto
