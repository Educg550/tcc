import re

from fastapi.testclient import TestClient

import app as app_module

cliente = TestClient(app_module.app)

CAMPOS = {
    "nome": ("NOME COMPLETO - SEM ABREVIAR", "nome_completo", "Maria Aparecida da Silva"),
    "n_usp": ("N. USP", "n_usp", "12345678"),
    "programa": ("PROGRAMA", "programa", "Ciência da Computação"),
    "email": ("E-MAIL", "email", "maria.silva@usp.br"),
    "nome_evento": ("NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "nome_evento", "Congresso Brasileiro de Computação"),
    "periodo": ("PERÍODO DO EVENTO, EXAME OU DEFESA", "periodo", "10 a 15 de outubro de 2024"),
    "cidade_evento": ("CIDADE DO EVENTO, EXAME OU DEFESA", "cidade_evento", "São Paulo"),
    "estado_evento": ("ESTADO DO EVENTO, EXAME OU DEFESA", "estado_evento", "SP"),
    "pais_evento": ("PAÍS DO EVENTO, EXAME OU DEFESA", "pais_evento", "Brasil"),
    "link_evento": ("LINK DO EVENTO, EXAME OU DEFESA", "link_evento", "https://evento.ime.usp.br"),
    "valor": ("VALOR SOLICITADO (R$)", "valor_solicitado", "R$ 1.500,00"),
    "detalhamento": ("DETALHAMENTO DO PEDIDO", "detalhamento", "Taxa de inscrição e passagens."),
    "apresentacao": ("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "apresentacao", "Apresentação oral"),
    "data_nascimento": ("DATA DE NASCIMENTO", "data_nascimento", "01/02/1980"),
    "logradouro": ("LOGRADOURO", "logradouro", "Av. Prof. Luciano Gualberto"),
    "numero": ("NÚMERO", "numero", "158"),
    "complemento": ("COMPLEMENTO", "complemento", "Bloco B"),
    "bairro": ("BAIRRO", "bairro", "Butantã"),
    "cep": ("CEP", "cep", "05508-090"),
    "cidade": ("CIDADE", "cidade", "São Paulo"),
    "estado": ("ESTADO", "estado", "SP"),
    "cpf": ("CPF (SEPARADOS POR PONTOS E TRAÇO)", "cpf", "111.444.777-35"),
    "rg": ("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "rg", "12.345.678-9"),
    "banco": ("NOME DO BANCO", "nome_banco", "Banco do Brasil"),
    "agencia": ("NÚMERO DA AGÊNCIA", "numero_agencia", "1234"),
    "conta": ("NÚMERO DA CONTA", "numero_conta", "12345-6"),
}

EXTRAS = {
    "nivel": ("NÍVEL", "nivel"),
    "tipo_auxilio": ("TIPO DE AUXÍLIO", "tipo_auxilio"),
}

VALORES_ABA = {
    "alunos": ("alunos", "ALUNOS", "aluno"),
    "docentes": ("docentes", "DOCENTES", "docente"),
}

_CONF = None
_ABA_ESCOLHIDA = {}


def _rotulo_e_snake(chave):
    if chave in CAMPOS:
        rotulo, snake, _ = CAMPOS[chave]
        return rotulo, snake
    return EXTRAS[chave]


def _valores_base(aba):
    valores = {chave: dados[2] for chave, dados in CAMPOS.items()}
    if aba == "alunos":
        valores["nivel"] = "Mestrado"
        valores["tipo_auxilio"] = "Participação em evento"
    return valores


def _dados(aba, variante, overrides=None):
    valores = _valores_base(aba)
    valores.update(overrides or {})
    dados = {}
    for chave, valor in valores.items():
        rotulo, snake = _rotulo_e_snake(chave)
        dados[rotulo if variante == "rotulo" else snake] = valor
    return dados


def _caminhos_post():
    caminhos = []
    for rota in app_module.app.routes:
        metodos = getattr(rota, "methods", None) or set()
        if "POST" in metodos:
            caminhos.append(rota.path)
    return caminhos


def _post(caminho, dados, codificacao):
    if codificacao == "json":
        return cliente.post(caminho, json=dados)
    return cliente.post(caminho, data=dados)


def _descobrir():
    for caminho in _caminhos_post():
        alvo = re.sub(r"\{[^}]+\}", "alunos", caminho)
        fixo = "{" not in caminho
        for codificacao in ("json", "data"):
            for variante in ("rotulo", "snake"):
                for valor in ("R$ 1.500,00", "150000"):
                    for chave_aba in (("aba", "tipo", None) if fixo else (None,)):
                        dados = _dados("alunos", variante, {"valor": valor})
                        if chave_aba:
                            dados[chave_aba] = "alunos"
                        resposta = _post(alvo, dados, codificacao)
                        if resposta.status_code == 200 and "Interessada" in resposta.text:
                            return {
                                "caminho": alvo,
                                "codificacao": codificacao,
                                "variante": variante,
                                "valor": valor,
                                "chave_aba": chave_aba,
                            }
    return None


def _conf():
    global _CONF
    if _CONF is None:
        _CONF = _descobrir()
    return _CONF


def _caminho_da_aba(aba, conf):
    for caminho in _caminhos_post():
        if aba[:5] in caminho.lower():
            return caminho
    return conf["caminho"]


def _valor_aba(aba, conf):
    chave = conf["chave_aba"]
    if not chave:
        return None
    if aba not in _ABA_ESCOLHIDA:
        escolhido = None
        caminho = _caminho_da_aba(aba, conf)
        for candidato in VALORES_ABA[aba]:
            dados = _dados(aba, conf["variante"], {"valor": conf["valor"]})
            dados[chave] = candidato
            resposta = _post(caminho, dados, conf["codificacao"])
            if resposta.status_code == 200 and "Interessada" in resposta.text:
                escolhido = candidato
                break
        _ABA_ESCOLHIDA[aba] = escolhido or VALORES_ABA[aba][0]
    return _ABA_ESCOLHIDA[aba]


def enviar(aba, overrides=None):
    conf = _conf()
    assert conf is not None, "endpoint de envio nao encontrado"
    overrides = dict(overrides or {})
    overrides.setdefault("valor", conf["valor"])
    dados = _dados(aba, conf["variante"], overrides)
    chave = conf["chave_aba"]
    if chave:
        dados[chave] = _valor_aba(aba, conf)
    return _post(_caminho_da_aba(aba, conf), dados, conf["codificacao"])


def _todos_vazios(aba):
    vazios = {chave: "" for chave in CAMPOS}
    if aba == "alunos":
        vazios["nivel"] = ""
        vazios["tipo_auxilio"] = ""
    return vazios


def test_erro_campo_obrigatorio_vazio():
    resposta = enviar("alunos", _todos_vazios("alunos"))
    assert "Preencha todos os campos" in resposta.text


def test_erro_de_campo_vazio_aparece_uma_unica_vez():
    resposta = enviar("alunos", _todos_vazios("alunos"))
    assert resposta.text.count("Preencha todos os campos") == 1


def test_erro_n_usp_nao_numerico():
    resposta = enviar("alunos", {"n_usp": "12a34"})
    assert "N. USP deve conter apenas números" in resposta.text


def test_erro_agencia_nao_numerica():
    resposta = enviar("alunos", {"agencia": "12-34"})
    assert "Número da agência deve conter apenas números" in resposta.text


def test_erro_valor_nao_positivo():
    resposta = enviar("alunos", {"valor": "R$ 0,00"})
    assert "Valor solicitado deve ser maior que 0" in resposta.text


def test_erro_email_invalido():
    resposta = enviar("alunos", {"email": "maria.usp.br"})
    assert "E-mail inválido" in resposta.text


def test_erro_cpf_fora_do_formato():
    resposta = enviar("alunos", {"cpf": "11144477735"})
    assert "CPF deve estar no formato 000.000.000-00" in resposta.text


def test_erro_cpf_digitos_verificadores():
    resposta = enviar("alunos", {"cpf": "111.444.777-34"})
    assert "CPF inválido" in resposta.text


def test_erro_cep_fora_do_formato():
    resposta = enviar("alunos", {"cep": "05508090"})
    assert "CEP deve estar no formato 00000-000" in resposta.text


def test_erro_data_fora_do_formato():
    resposta = enviar("alunos", {"data_nascimento": "01-02-1980"})
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.text


def test_erro_data_inexistente():
    resposta = enviar("alunos", {"data_nascimento": "31/02/1980"})
    assert "Data de nascimento inválida" in resposta.text


def test_varios_erros_de_uma_vez():
    resposta = enviar("alunos", {"n_usp": "abc", "agencia": "abc", "email": "x"})
    texto = resposta.text
    assert "N. USP deve conter apenas números" in texto
    assert "Número da agência deve conter apenas números" in texto
    assert "E-mail inválido" in texto


def test_sem_oficio_quando_ha_erro():
    resposta = enviar("alunos", {"n_usp": "abc"})
    assert "Interessada(o)" not in resposta.text


def test_oficio_alunos_completo():
    texto = enviar("alunos").text
    assert "Interessada(o): Maria Aparecida da Silva - 12345678" in texto
    assert "E-mail: maria.silva@usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Período: 10 a 15 de outubro de 2024" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Link do evento: https://evento.ime.usp.br" in texto
    assert "Apresentação de trabalho: Apresentação oral" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Taxa de inscrição e passagens." in texto
    assert "Av. Prof. Luciano Gualberto, 158" in texto
    assert "Complemento: Bloco B" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 111.444.777-35" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 12345-6" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_docentes():
    texto = enviar("docentes").text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação - Mestrado" not in texto
    assert "Interessada(o): Maria Aparecida da Silva - 12345678" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_link_e_complemento_vazios_saem_do_oficio():
    texto = enviar("alunos", {"link_evento": "", "complemento": ""}).text
    assert "Interessada(o)" in texto
    assert "Link do evento" not in texto
    assert "Complemento:" not in texto
