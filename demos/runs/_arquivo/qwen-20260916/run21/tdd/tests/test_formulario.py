from conftest import _cliente


ROTULOS_ALUNOS = [
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

ROTULOS_DOCENTES = [r for r in ROTULOS_ALUNOS if r not in ("NÍVEL", "TIPO DE AUXÍLIO")]

OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]


def _html():
    resp = _cliente().get("/")
    assert resp.status_code == 200
    return resp.text


def teste_rotulos_aba_alunos():
    html = _html()
    for rotulo in ROTULOS_ALUNOS:
        assert rotulo in html
    for opcao in OPCOES:
        assert opcao in html


def teste_rotulos_aba_docentes():
    html = _html()
    for rotulo in ROTULOS_DOCENTES:
        assert html.count(rotulo) >= 2


def teste_botao_enviar():
    html = _html()
    assert html.count("Enviar solicitação") >= 2
