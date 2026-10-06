import datetime


def gerar_oficio(d, tipo):
    linhas = []
    linhas.append(f"Interessada(o): {d['nome']} - {d['n_usp']}")
    linhas.append(f"E-mail: {d['email']}")
    if tipo == "aluno":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}")
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d['programa']}")
    linhas.append("")
    linhas.append("A CCP-" + d['programa'] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {d['evento']}")
    linhas.append(f"Período: {d['periodo']}")
    linhas.append(f"Local: {d['cidade']} - {d['estado']} - {d['pais']}")
    if d.get('link'):
        linhas.append(f"Link do evento: {d['link']}")
    linhas.append(f"Apresentação de trabalho: {d['apresentacao']}")
    linhas.append(f"Valor solicitado: {d['valor']}")
    linhas.append(f"Detalhamento: {d['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['logradouro']}, {d['numero']}")
    if d.get('complemento'):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas.append(f"CEP: {d['cep']}")
    linhas.append(f"{d['bairro']}, {d['cidade_end']} - {d['estado_end']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d['nascimento']}")
    linhas.append(f"CPF: {d['cpf']}")
    linhas.append(f"RG / RNM: {d['rg']}")
    linhas.append(f"Banco: {d['banco']}")
    linhas.append(f"Agência: {d['agencia']}")
    linhas.append(f"Conta: {d['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)
