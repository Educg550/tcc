"""Montagem do ofício de solicitação de auxílio financeiro."""

from util import formatar_moeda


def _linha(valor, rotulo):
    if valor:
        return f"{rotulo}{valor}\n"
    return ""


def gerar_oficio(aba, c, hoje):
    data = hoje.strftime("%d/%m/%Y")
    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {c['programa']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {c['tipo']}"
        programa = f"Programa: {c['programa']} - {c['nivel']}"

    local = (
        f"Local: {c['evento_cidade']} - {c['evento_estado']} - {c['evento_pais']}"
    )

    oficio = (
        "\n"
        f"Interessada(o): {c['nome']} - {c['nusp']}\n"
        f"E-mail: {c['email']}\n"
        f"Assunto: {assunto}\n"
        f"{programa}\n"
        "\n"
        f"A CCP-{c['programa']} aprovou na data de hoje ({data}), a solicitação de "
        "auxílio financeiro para a interessada(o) acima, conforme segue:\n"
        "\n"
        "Dados do evento\n"
        f"Evento: {c['evento_nome']}\n"
        f"Período: {c['evento_periodo']}\n"
        f"{local}\n"
        f"{_linha(c['evento_link'], 'Link do evento: ')}"
        f"Apresentação de trabalho: {c['apresentacao']}\n"
        f"Valor solicitado: {formatar_moeda(c['valor'])}\n"
        f"Detalhamento: {c['detalhamento']}\n"
        "\n"
        "Endereço da(o) interessada(o)\n"
        f"{c['logradouro']}, {c['numero']}\n"
        f"{_linha(c['complemento'], 'Complemento: ')}"
        f"CEP: {c['cep']}\n"
        f"{c['bairro']}, {c['cidade']} - {c['estado']}\n"
        "\n"
        "Dados para pagamento\n"
        f"Data de nascimento: {c['nascimento']}\n"
        f"CPF: {c['cpf']}\n"
        f"RG / RNM: {c['rg']}\n"
        f"Banco: {c['banco']}\n"
        f"Agência: {c['agencia']}\n"
        f"Conta: {c['conta']}\n"
        "\n"
        "Encaminhe-se ao Serviço Financeiro para providências.\n"
    )
    return oficio
