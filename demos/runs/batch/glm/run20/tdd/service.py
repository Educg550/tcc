import re
from datetime import date


def validar(dados: dict, aba: str) -> list[str]:
    erros = []

    obrigatorios = [
        "nome_completo", "n_usp", "programa", "email",
        "nome_do_evento", "periodo_do_evento", "cidade_do_evento",
        "estado_do_evento", "pais_do_evento", "valor_solicitado",
        "detalhamento_do_pedido", "apresentacao_de_trabalho",
        "data_de_nascimento", "logradouro", "numero", "bairro",
        "cep", "cidade", "estado", "cpf", "rg", "banco",
        "agencia", "conta",
    ]
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_de_auxilio"]

    faltando = [c for c in obrigatorios if not str(dados.get(c, "") or "").strip()]
    if faltando:
        erros.append("Preencha todos os campos")

    n_usp = str(dados.get("n_usp", "") or "")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", "") or "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("valor_solicitado", "") or "").replace("$", "").replace(",", "").replace(".", "")
    if valor and (not valor.isdigit() or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", "") or "")
    if email:
        usuario, _, dominio = email.partition("@")
        if not usuario or not dominio or "." not in dominio:
            erros.append("E-mail inválido")

    cpf = str(dados.get("cpf", "") or "")
    cpf_match = re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf)
    if cpf and not cpf_match:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf_match and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = str(dados.get("cep", "") or "")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = str(dados.get("data_de_nascimento", "") or "")
    data_match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", nascimento)
    if nascimento and not data_match:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data_match:
        d, m, a = (int(g) for g in data_match.groups())
        try:
            date(a, m, d)
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(set(digitos[:9])) == 1:
        return False
    for i in (9, 10):
        soma = sum(d * w for d, w in zip(digitos[:i], range(i + 1, 1, -1)))
        resto = (soma * 10) % 11
        esperado = 0 if resto == 10 else resto
        if digitos[i] != esperado:
            return False
    return True


def _moeda(texto: str) -> str:
    digitos = re.sub(r"\D", "", str(texto or ""))
    if not digitos:
        return ""
    centavos = int(digitos)
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,},{resto:02d}".replace(",", ".")


def montar_oficio(dados: dict, aba: str) -> str:
    alunos = aba == "alunos"
    linhas = []
    linhas.append(f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}")
    linhas.append(f"E-mail: {dados['email']}")
    if alunos:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_de_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    linhas.append("")
    linhas.append(
        f"A CCP-{dados['programa']} aprovou na data de hoje, "
        f"a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {dados['nome_do_evento']}")
    linhas.append(f"Período: {dados['periodo_do_evento']}")
    linhas.append(f"Local: {dados['cidade_do_evento']} - {dados['estado_do_evento']} - {dados['pais_do_evento']}")
    if str(dados.get("link_do_evento", "") or "").strip():
        linhas.append(f"Link do evento: {dados['link_do_evento']}")
    linhas.append(f"Apresentação de trabalho: {dados['apresentacao_de_trabalho']}")
    linhas.append(f"Valor solicitado: {_moeda(dados['valor_solicitado'])}")
    linhas.append(f"Detalhamento: {dados['detalhamento_do_pedido']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{dados['logradouro']}, {dados['numero']}")
    if str(dados.get("complemento", "") or "").strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.append(f"CEP: {dados['cep']}")
    linhas.append(f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {dados['data_de_nascimento']}")
    linhas.append(f"CPF: {dados['cpf']}")
    linhas.append(f"RG / RNM: {dados['rg']}")
    linhas.append(f"Banco: {dados['banco']}")
    linhas.append(f"Agência: {dados['agencia']}")
    linhas.append(f"Conta: {dados['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)
