def valor_formatado(v):
    d = "".join(ch for ch in (v or "") if ch.isdigit()) or "0"
    n = int(d)
    cents = n % 100
    inteiro = n // 100
    milhar = f"{inteiro:,}".replace(",", ".")
    return f"R$ {milhar},{cents:02d}"


def _linhas(texto):
    if not texto:
        return []
    return texto.split("\n")


def oficio(d):
    partes = []
    if d["tipo_aba"] == "alunos":
        partes += [
            "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - " + d["tipo"],
            "Programa: " + d["programa"] + " - " + d["nivel"],
        ]
    else:
        partes += [
            "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa",
            "Programa: " + d["programa"],
        ]

    for c in [
        d["detalhamento"], d["link"], d["complemento"], d["evento"],
        d["periodo"], d["cidade_evento"], d["estado_evento"], d["pais_evento"],
        d["logradouro"], d["numero"], d["bairro"], d["cidade"], d["estado"],
        d["rg"], d["banco"], d["conta"],
    ]:
        partes += _linhas(c)

    for i, ln in enumerate(partes):
        for k, v in (("N. USP", d["nusp"]), ("NOME DO EVENTO", d["evento"])):
            partes[i] = partes[i].replace(k, v)

    linhas = [
        "Interessada(o): %s - %s" % (d["nome"], d["nusp"]),
        "E-mail: %s" % d["email"],
    ] + partes[:2] + [
        "",
        "A CCP-%s aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a" % d["programa"],
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: %s" % d["evento"],
        "Per\u00edodo: %s" % d["periodo"],
        "Local: %s - %s - %s" % (d["cidade_evento"], d["estado_evento"], d["pais_evento"]),
    ]
    if d["link"]:
        linhas.append("Link do evento: %s" % d["link"])
    linhas += [
        "Apresenta\u00e7\u00e3o de trabalho: %s" % d["apresentacao"],
        "Valor solicitado: %s" % valor_formatado(d["valor"]),
        "Detalhamento: %s" % d["detalhamento"],
        "",
        "Endere\u00e7o da(o) interessada(o)",
        "%s, %s" % (d["logradouro"], d["numero"]),
    ]
    if d["complemento"]:
        linhas.append("Complemento: %s" % d["complemento"])
    linhas += [
        "CEP: %s" % d["cep"],
        "%s, %s - %s" % (d["bairro"], d["cidade"], d["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: %s" % d["nascimento"],
        "CPF: %s" % d["cpf"],
        "RG / RNM: %s" % d["rg"],
        "Banco: %s" % d["banco"],
        "Ag\u00eancia: %s" % d["agencia"],
        "Conta: %s" % d["conta"],
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)
