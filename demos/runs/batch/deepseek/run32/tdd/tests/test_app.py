import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

import app as aplicacao

cliente = TestClient(aplicacao.app)

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

GRUPOS = [
    ("alunos", ["aba", "formulario", "tipo_solicitante"]),
    ("Maria da Silva", ["nome_completo", "nomeCompleto"]),
    ("12345678", ["n_usp", "nusp", "numero_usp"]),
    ("Matemática Aplicada", ["programa"]),
    ("Doutorado", ["nivel"]),
    ("Participação em evento", ["tipo_auxilio"]),
    ("maria@ime.usp.br", ["email"]),
    ("Congresso Brasileiro de Matemática", ["nome_evento"]),
    ("10 a 15 de julho de 2024", ["periodo_evento"]),
    ("Rio de Janeiro", ["cidade_evento"]),
    ("RJ", ["estado_evento"]),
    ("Brasil", ["pais_evento"]),
    ("https://evento.ime.usp.br", ["link_evento"]),
    ("R$ 1.500,00", ["valor_solicitado"]),
    ("Passagem aérea e hospedagem", ["detalhamento"]),
    ("Apresentação oral", ["apresentacao"]),
    ("01/02/1980", ["data_nascimento"]),
    ("Rua do Matão", ["logradouro"]),
    ("1010", ["numero"]),
    ("", ["complemento"]),
    ("Cidade Universitária", ["bairro"]),
    ("05508-090", ["cep"]),
    ("São Paulo", ["cidade"]),
    ("SP", ["estado"]),
    ("123.456.789-09", ["cpf"]),
    ("12.345.678-9", ["rg"]),
    ("Banco do Brasil", ["banco"]),
    ("1234", ["agencia"]),
    ("12345-6", ["conta"]),
]


def _dados(**alteracoes):
    dados = {}
    for padrao, nomes in GRUPOS:
        valor = alteracoes.get(nomes[0], padrao)
        for nome in nomes:
            dados[nome] = valor
    return dados


def _caminho_envio():
    for caminho, operacoes in aplicacao.app.openapi().get("paths", {}).items():
        if "post" in operacoes:
            return caminho
    raise AssertionError("a aplicação não expõe rota de envio (POST)")


def _enviar(dados):
    caminho = _caminho_envio()
    resposta = cliente.post(caminho, json=dados)
    if resposta.status_code == 422:
        detalhe = resposta.json().get("detail")
        if isinstance(detalhe, list) and detalhe and isinstance(detalhe[0], dict):
            resposta = cliente.post(caminho, data=dados)
    return resposta


def _texto(resposta):
    try:
        conteudo = resposta.json()
    except ValueError:
        return resposta.text
    valores = []

    def coletar(valor):
        if isinstance(valor, str):
            valores.append(valor)
        elif isinstance(valor, dict):
            for item in valor.values():
                coletar(item)
        elif isinstance(valor, list):
            for item in valor:
                coletar(item)

    coletar(conteudo)
    return "\n".join(valores)


def test_pagina_inicial_serve_o_formulario():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_abas_alunos_e_docentes_nesta_ordem():
    html = cliente.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cabecalho_institucional_da_universidade():
    html = cliente.get("/").text
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_blocos_de_campos_tem_titulo_visivel():
    html = cliente.get("/").text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


@pytest.mark.parametrize("rotulo", ROTULOS)
def test_rotulo_visivel_na_pagina(rotulo):
    assert rotulo in cliente.get("/").text


def test_cada_aba_tem_o_botao_enviar_solicitacao():
    html = cliente.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_cores_da_universidade_no_css():
    css = cliente.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_javascript_servido():
    resposta = cliente.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip()


def test_logotipo_servido_dos_assets():
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content.startswith(b"\x89PNG")


def test_envio_valido_gera_o_oficio_com_os_dados():
    resposta = _enviar(_dados())
    assert resposta.status_code == 200
    texto = _texto(resposta)
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Matemática Aplicada - Doutorado" in texto
    assert "Dados do evento" in texto
    assert "Evento: Congresso Brasileiro de Matemática" in texto
    assert "Período: 10 a 15 de julho de 2024" in texto
    assert "Local: Rio de Janeiro - RJ - Brasil" in texto
    assert "Link do evento: https://evento.ime.usp.br" in texto
    assert "Apresentação de trabalho: Apresentação oral" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem aérea e hospedagem" in texto
    assert "Rua do Matão, 1010" in texto
    assert "CEP: 05508-090" in texto
    assert "Cidade Universitária, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_da_aba_docentes_usa_a_verba_do_programa():
    texto = _texto(_enviar(_dados(aba="docentes")))
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática Aplicada" in texto
    assert "Programa: Matemática Aplicada - Doutorado" not in texto


def test_campos_opcionais_vazios_saem_do_oficio():
    texto = _texto(_enviar(_dados(link_evento="", complemento="")))
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_campo_obrigatorio_vazio():
    assert "Preencha todos os campos" in _texto(_enviar(_dados(nome_completo="")))


def test_n_usp_deve_conter_apenas_numeros():
    assert "N. USP deve conter apenas números" in _texto(_enviar(_dados(n_usp="12a34")))


def test_agencia_deve_conter_apenas_numeros():
    assert "Número da agência deve conter apenas números" in _texto(_enviar(_dados(agencia="12-4")))


def test_valor_solicitado_deve_ser_maior_que_zero():
    assert "Valor solicitado deve ser maior que 0" in _texto(_enviar(_dados(valor_solicitado="R$ 0,00")))


def test_email_invalido():
    assert "E-mail inválido" in _texto(_enviar(_dados(email="maria.ime.usp.br")))


def test_cpf_fora_do_formato():
    assert "CPF deve estar no formato 000.000.000-00" in _texto(_enviar(_dados(cpf="12345678909")))


def test_cep_fora_do_formato():
    assert "CEP deve estar no formato 00000-000" in _texto(_enviar(_dados(cep="05508090")))


def test_data_de_nascimento_fora_do_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _texto(_enviar(_dados(data_nascimento="01021980")))


def test_cpf_com_digitos_verificadores_invalidos():
    assert "CPF inválido" in _texto(_enviar(_dados(cpf="123.456.789-00")))


def test_data_de_nascimento_inexistente():
    assert "Data de nascimento inválida" in _texto(_enviar(_dados(data_nascimento="31/02/1980")))


def test_todas_as_mensagens_de_erro_aparecem_juntas():
    texto = _texto(_enviar(_dados(n_usp="abc", email="invalido")))
    assert "N. USP deve conter apenas números" in texto
    assert "E-mail inválido" in texto


def test_envio_com_erro_nao_gera_o_oficio():
    assert "Interessada(o):" not in _texto(_enviar(_dados(email="maria.ime.usp.br")))
