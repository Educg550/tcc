import re


def get_forms(html):
    forms = re.findall(r"<form.*?</form>", html, re.DOTALL)
    assert len(forms) == 2, f"esperava 2 formularios, encontrou {len(forms)}"
    return forms[0], forms[1]


def _tail_after_label(html, label):
    pattern = r"<label[^>]*>\s*" + re.escape(label) + r"\s*(?=<)"
    m = re.search(pattern, html)
    assert m is not None, f"rotulo nao encontrado: {label}"
    tail = html[m.end():]
    next_label = tail.find("<label")
    return tail if next_label == -1 else tail[:next_label]


def name_after_label(html, label):
    window = _tail_after_label(html, label)
    m = re.search(r'name="([^"]+)"', window)
    assert m is not None, f"atributo name nao encontrado para o rotulo: {label}"
    return m.group(1)


def placeholder_after_label(html, label):
    window = _tail_after_label(html, label)
    m = re.search(r'placeholder="([^"]*)"', window)
    assert m is not None, f"placeholder nao encontrado para o rotulo: {label}"
    return m.group(1)


def select_field(html, label, option_text):
    window = _tail_after_label(html, label)
    sel = re.search(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', window, re.DOTALL)
    assert sel is not None, f"select nao encontrado para o rotulo: {label}"
    name = sel.group(1)
    block = sel.group(2)
    opt = re.search(
        r'<option[^>]*value="([^"]*)"[^>]*>\s*' + re.escape(option_text) + r'\s*</option>',
        block,
    )
    if opt is not None:
        return name, opt.group(1)
    if option_text in block:
        return name, option_text
    raise AssertionError(f"opcao '{option_text}' nao encontrada para o rotulo: {label}")


def hidden_fields(form_html):
    fields = {}
    for tag in re.findall(r"<input[^>]*>", form_html):
        if 'type="hidden"' in tag:
            name_m = re.search(r'name="([^"]+)"', tag)
            value_m = re.search(r'value="([^"]*)"', tag)
            if name_m:
                fields[name_m.group(1)] = value_m.group(1) if value_m else ""
    return fields


def form_action(form_html):
    m = re.search(r'<form[^>]*action="([^"]*)"', form_html)
    if m and m.group(1):
        return m.group(1)
    return "/"


def build_payload(form_html, aba):
    data = {}
    data.update(hidden_fields(form_html))

    def L(label, value):
        data[name_after_label(form_html, label)] = value

    L("NOME COMPLETO - SEM ABREVIAR", "Maria da Silva Santos")
    L("N. USP", "9876543")
    L("PROGRAMA", "Ciência da Computação" if aba == "alunos" else "Direito")
    if aba == "alunos":
        name, value = select_field(form_html, "NÍVEL", "Mestrado")
        data[name] = value
        name, value = select_field(form_html, "TIPO DE AUXÍLIO", "Participação em evento")
        data[name] = value
    L("E-MAIL", "maria.silva@usp.br")
    L("NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "Congresso Brasileiro de Computação")
    L("PERÍODO DO EVENTO, EXAME OU DEFESA", "10/03/2024 a 15/03/2024")
    L("CIDADE DO EVENTO, EXAME OU DEFESA", "Fortaleza")
    L("ESTADO DO EVENTO, EXAME OU DEFESA", "CE")
    L("PAÍS DO EVENTO, EXAME OU DEFESA", "Brasil")
    L("LINK DO EVENTO, EXAME OU DEFESA", "https://evento.exemplo.br")
    L("VALOR SOLICITADO (R$)", "R$ 1.500,00")
    L("DETALHAMENTO DO PEDIDO", "Solicito auxílio para participação no evento.")
    name, value = select_field(
        form_html, "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "Pôster"
    )
    data[name] = value
    L("DATA DE NASCIMENTO", "01/02/1980")
    L("LOGRADOURO", "Rua das Flores")
    L("NÚMERO", "123")
    L("COMPLEMENTO", "Apto 45")
    L("BAIRRO", "Butantã")
    L("CEP", "05508-090")
    L("CIDADE", "São Paulo")
    L("ESTADO", "SP")
    L("CPF (SEPARADOS POR PONTOS E TRAÇO)", "123.456.789-01")
    L("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "12.345.678-9")
    L("NOME DO BANCO", "Banco do Brasil")
    L("NÚMERO DA AGÊNCIA", "1234")
    L("NÚMERO DA CONTA", "56789-0")
    return data
