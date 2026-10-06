from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import html
import re

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

BLOCK1_BEFORE = [
    {"name": "nome", "label": "NOME COMPLETO - SEM ABREVIAR", "type": "text", "placeholder": "Ex.: Fulano de Tal"},
    {"name": "nusp", "label": "N. USP", "type": "text", "placeholder": "Ex.: 12345678", "inputmode": "numeric"},
    {"name": "programa", "label": "PROGRAMA", "type": "text", "placeholder": "Ex.: Ciência da Computação"},
]

BLOCK1_ALUNO = [
    {"name": "nivel", "label": "NÍVEL", "type": "select", "options": ["Mestrado", "Doutorado"], "placeholder_option": "Selecione o nível"},
    {"name": "tipo_auxilio", "label": "TIPO DE AUXÍLIO", "type": "select", "options": ["Participação em evento", "Banca de exame ou defesa", "Outro"], "placeholder_option": "Selecione o tipo"},
]

BLOCK1_AFTER = [
    {"name": "email", "label": "E-MAIL", "type": "text", "placeholder": "Ex.: fulano@usp.br"},
    {"name": "evento", "label": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "type": "text", "placeholder": "Ex.: Congresso Nacional de Matemática"},
    {"name": "periodo", "label": "PERÍODO DO EVENTO, EXAME OU DEFESA", "type": "text", "placeholder": "Ex.: 01/01/2024 a 05/01/2024"},
    {"name": "cidade_evento", "label": "CIDADE DO EVENTO, EXAME OU DEFESA", "type": "text", "placeholder": "Ex.: São Paulo"},
    {"name": "estado_evento", "label": "ESTADO DO EVENTO, EXAME OU DEFESA", "type": "text", "placeholder": "Ex.: SP"},
    {"name": "pais_evento", "label": "PAÍS DO EVENTO, EXAME OU DEFESA", "type": "text", "placeholder": "Ex.: Brasil"},
    {"name": "link_evento", "label": "LINK DO EVENTO, EXAME OU DEFESA", "type": "text", "placeholder": "Ex.: https://evento.usp.br"},
    {"name": "valor", "label": "VALOR SOLICITADO (R$)", "type": "text", "placeholder": "Ex.: R$ 1.500,00", "inputmode": "numeric"},
    {"name": "detalhamento", "label": "DETALHAMENTO DO PEDIDO", "type": "textarea", "placeholder": "Ex.: Passagem aérea e inscrição no evento."},
    {"name": "apresentacao", "label": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "type": "select", "options": ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"], "placeholder_option": "Selecione uma opção"},
]

BLOCK2 = [
    {"name": "data_nasc", "label": "DATA DE NASCIMENTO", "type": "text", "placeholder": "Ex.: 01/02/1980", "inputmode": "numeric", "maxlength": "10"},
    {"name": "logradouro", "label": "LOGRADOURO", "type": "text", "placeholder": "Ex.: Rua do Matão"},
    {"name": "numero", "label": "NÚMERO", "type": "text", "placeholder": "Ex.: 1010"},
    {"name": "complemento", "label": "COMPLEMENTO", "type": "text", "placeholder": "Ex.: Bloco B, apto 123"},
    {"name": "bairro", "label": "BAIRRO", "type": "text", "placeholder": "Ex.: Cidade Universitária"},
    {"name": "cep", "label": "CEP", "type": "text", "placeholder": "Ex.: 05508-090", "inputmode": "numeric", "maxlength": "9"},
    {"name": "cidade_end", "label": "CIDADE", "type": "text", "placeholder": "Ex.: São Paulo"},
    {"name": "estado_end", "label": "ESTADO", "type": "text", "placeholder": "Ex.: SP"},
]

BLOCK3 = [
    {"name": "cpf", "label": "CPF (SEPARADOS POR PONTOS E TRAÇO)", "type": "text", "placeholder": "Ex.: 123.456.789-01", "inputmode": "numeric", "maxlength": "14"},
    {"name": "rg", "label": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "type": "text", "placeholder": "Ex.: 00.000.000-0"},
    {"name": "banco", "label": "NOME DO BANCO", "type": "text", "placeholder": "Ex.: Banco do Brasil"},
    {"name": "agencia", "label": "NÚMERO DA AGÊNCIA", "type": "text", "placeholder": "Ex.: 1234", "inputmode": "numeric"},
    {"name": "conta", "label": "NÚMERO DA CONTA", "type": "text", "placeholder": "Ex.: 12345-6"},
]

def generate_field_html(field, value):
    name = field["name"]
    label = field["label"]
    type_ = field.get("type", "text")
    placeholder = field.get("placeholder", "")
    inputmode = field.get("inputmode", "")
    maxlength = field.get("maxlength", "")
    escaped_value = html.escape(value if value is not None else "")
    
    if type_ == "select":
        options = field.get("options", [])
        placeholder_option = field.get("placeholder_option", "Selecione...")
        options_html = f'<option value="" disabled {"selected" if not value else ""}>{html.escape(placeholder_option)}</option>'
        for option in options:
            selected = ' selected' if value == option else ''
            options_html += f'<option value="{html.escape(option)}"{selected}>{html.escape(option)}</option>'
        return f'''
        <div class="form-group">
            <label for="{name}">{label}</label>
            <select id="{name}" name="{name}">
                {options_html}
            </select>
        </div>'''
    elif type_ == "textarea":
        return f'''
        <div class="form-group">
            <label for="{name}">{label}</label>
            <textarea id="{name}" name="{name}" placeholder="{html.escape(placeholder)}">{escaped_value}</textarea>
        </div>'''
    else:
        attrs = []
        if inputmode:
            attrs.append(f'inputmode="{inputmode}"')
        if maxlength:
            attrs.append(f'maxlength="{maxlength}"')
        attrs_str = ' '.join(attrs)
        return f'''
        <div class="form-group">
            <label for="{name}">{label}</label>
            <input type="text" id="{name}" name="{name}" placeholder="{html.escape(placeholder)}" value="{escaped_value}" {attrs_str}>
        </div>'''

def generate_block_html(fields, values):
    html_parts = []
    for field in fields:
        html_parts.append(generate_field_html(field, values.get(field["name"], "")))
    return "\n".join(html_parts)

def render_form_page(data, active_tab, errors):
    values = {key: data.get(key, "") for key in data}
    if errors:
        error_items = "".join([f'<div class="error">{html.escape(err)}</div>' for err in errors])
        error_html = f'<div class="error-messages" role="alert">{error_items}</div>'
    else:
        error_html = ""
    
    if active_tab == "ALUNOS":
        tab_alunos_class = "active"
        tab_alunos_aria = "true"
        tab_docentes_class = ""
        tab_docentes_aria = "false"
        aluno_fields_display = "block"
    else:
        tab_alunos_class = ""
        tab_alunos_aria = "false"
        tab_docentes_class = "active"
        tab_docentes_aria = "true"
        aluno_fields_display = "none"
    
    block1_before_html = generate_block_html(BLOCK1_BEFORE, values)
    block1_aluno_html = generate_block_html(BLOCK1_ALUNO, values)
    block1_after_html = generate_block_html(BLOCK1_AFTER, values)
    block2_html = generate_block_html(BLOCK2, values)
    block3_html = generate_block_html(BLOCK3, values)
    
    fieldset1 = f'''<fieldset>
        <legend>SOLICITANTE E EVENTO</legend>
        {block1_before_html}
        <div id="alunoFields" style="display: {aluno_fields_display};">
            {block1_aluno_html}
        </div>
        {block1_after_html}
    </fieldset>'''
    fieldset2 = f'''<fieldset>
        <legend>ENDEREÇO DO SOLICITANTE</legend>
        {block2_html}
    </fieldset>'''
    fieldset3 = f'''<fieldset>
        <legend>INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</legend>
        {block3_html}
    </fieldset>'''
    
    html = f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Solicitação de Auxílio Financeiro</title>
<style>
    :root {{
        --usp-blue: #002D72;
        --usp-light: #f5f5f5;
        --border: #ccc;
    }}
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: var(--usp-light);
        color: #333;
        line-height: 1.6;
    }}
    .container {{
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }}
    header.institutional {{
        background-color: var(--usp-blue);
        color: white;
        padding: 20px 0;
        margin-bottom: 30px;
    }}
    header.institutional h1 {{
        font-size: 2em;
        font-weight: 700;
    }}
    header.institutional p {{
        font-size: 1.1em;
        margin-top: 5px;
    }}
    .tabs {{
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }}
    .tab {{
        padding: 10px 30px;
        background-color: #e0e0e0;
        border: 2px solid var(--usp-blue);
        border-radius: 5px 5px 0 0;
        cursor: pointer;
        font-weight: bold;
        font-size: 1.1em;
        color: var(--usp-blue);
    }}
    .tab.active {{
        background-color: var(--usp-blue);
        color: white;
        border-bottom: none;
    }}
    .tab:focus {{
        outline: 2px solid orange;
    }}
    .error-messages {{
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 10px;
        margin-bottom: 20px;
        border-radius: 5px;
    }}
    .error {{
        margin-bottom: 5px;
    }}
    fieldset {{
        background: white;
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 30px;
    }}
    legend {{
        font-weight: bold;
        font-size: 1.2em;
        color: var(--usp-blue);
        padding: 0 10px;
    }}
    .form-group {{
        margin-bottom: 15px;
    }}
    label {{
        display: block;
        margin-bottom: 5px;
        font-weight: 600;
    }}
    input[type="text"],
    select,
    textarea {{
        width: 100%;
        padding: 10px;
        border: 1px solid var(--border);
        border-radius: 4px;
        font-size: 1em;
    }}
    textarea {{
        min-height: 100px;
        resize: vertical;
    }}
    .form-actions {{
        text-align: right;
        margin-top: 20px;
    }}
    .btn-submit {{
        background-color: var(--usp-blue);
        color: white;
        padding: 12px 30px;
        border: none;
        border-radius: 4px;
        font-size: 1.1em;
        cursor: pointer;
        font-weight: bold;
    }}
    .btn-submit:hover {{
        background-color: #001b4d;
    }}
</style>
</head>
<body>
<header class="institutional">
    <div class="container">
        <h1>Universidade de São Paulo</h1>
        <p>Instituto de Matemática e Estatística</p>
    </div>
</header>
<main class="container">
    <div class="tabs" role="tablist">
        <button class="tab {tab_alunos_class}" id="tabAlunos" data-tab="ALUNOS" role="tab" aria-selected="{tab_alunos_aria}">ALUNOS</button>
        <button class="tab {tab_docentes_class}" id="tabDocentes" data-tab="DOCENTES" role="tab" aria-selected="{tab_docentes_aria}">DOCENTES</button>
    </div>
    {error_html}
    <form id="formSolicitacao" method="post" action="/">
        <input type="hidden" name="aba" id="aba" value="{active_tab}">
        {fieldset1}
        {fieldset2}
        {fieldset3}
        <div class="form-actions">
            <button type="submit" class="btn-submit">Enviar solicitação</button>
        </div>
    </form>
</main>
<script>
function formatValor(input) {{
    let digits = input.value.replace(/\\D/g, '');
    if (digits.length === 0) {{
        input.value = '';
        return;
    }}
    let cents = parseInt(digits, 10);
    if (isNaN(cents)) cents = 0;
    let reais = cents / 100;
    let formatted = reais.toLocaleString('pt-BR', {{ style: 'currency', currency: 'BRL' }});
    input.value = formatted;
}}

function formatCPF(input) {{
    let digits = input.value.replace(/\\D/g, '');
    if (digits.length === 11) {{
        input.value = digits.replace(/(\\d{{3}})(\\d{{3}})(\\d{{3}})(\\d{{2}})/, '$1.$2.$3-$4');
    }}
}}

function formatCEP(input) {{
    let digits = input.value.replace(/\\D/g, '');
    if (digits.length === 8) {{
        input.value = digits.replace(/(\\d{{5}})(\\d{{3}})/, '$1-$2');
    }}
}}

function formatDataNasc(input) {{
    let digits = input.value.replace(/\\D/g, '');
    if (digits.length === 8) {{
        input.value = digits.replace(/(\\d{{2}})(\\d{{2}})(\\d{{4}})/, '$1/$2/$3');
    }}
}}

document.addEventListener('DOMContentLoaded', function() {{
    const tabAlunos = document.getElementById('tabAlunos');
    const tabDocentes = document.getElementById('tabDocentes');
    const alunoFields = document.getElementById('alunoFields');
    const abaInput = document.getElementById('aba');

    function setActiveTab(tab) {{
        if (tab === 'ALUNOS') {{
            tabAlunos.classList.add('active');
            tabDocentes.classList.remove('active');
            tabAlunos.setAttribute('aria-selected', 'true');
            tabDocentes.setAttribute('aria-selected', 'false');
            alunoFields.style.display = 'block';
            abaInput.value = 'ALUNOS';
        }} else {{
            tabDocentes.classList.add('active');
            tabAlunos.classList.remove('active');
            tabDocentes.setAttribute('aria-selected', 'true');
            tabAlunos.setAttribute('aria-selected', 'false');
            alunoFields.style.display = 'none';
            abaInput.value = 'DOCENTES';
        }}
    }}

    tabAlunos.addEventListener('click', function() {{ setActiveTab('ALUNOS'); }});
    tabDocentes.addEventListener('click', function() {{ setActiveTab('DOCENTES'); }});

    setActiveTab(abaInput.value);

    document.getElementById('valor').addEventListener('blur', function() {{ formatValor(this); }});
    document.getElementById('cpf').addEventListener('blur', function() {{ formatCPF(this); }});
    document.getElementById('cep').addEventListener('blur', function() {{ formatCEP(this); }});
    document.getElementById('data_nasc').addEventListener('blur', function() {{ formatDataNasc(this); }});
}});
</script>
</body>
</html>'''
    return html

def render_confirmation_page(oficio):
    oficio_escaped = html.escape(oficio)
    html = f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Solicitação registrada</title>
<style>
    :root {{
        --usp-blue: #002D72;
        --usp-light: #f5f5f5;
    }}
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: var(--usp-light);
        color: #333;
        line-height: 1.6;
    }}
    .container {{
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }}
    header.institutional {{
        background-color: var(--usp-blue);
        color: white;
        padding: 20px 0;
        margin-bottom: 30px;
    }}
    header.institutional h1 {{
        font-size: 2em;
        font-weight: 700;
    }}
    header.institutional p {{
        font-size: 1.1em;
        margin-top: 5px;
    }}
    h2 {{
        color: var(--usp-blue);
        margin-bottom: 20px;
    }}
    pre {{
        background: white;
        border: 1px solid #ccc;
        padding: 20px;
        white-space: pre-wrap;
        word-wrap: break-word;
        border-radius: 5px;
        font-family: 'Courier New', Courier, monospace;
    }}
</style>
</head>
<body>
<header class="institutional">
    <div class="container">
        <h1>Universidade de São Paulo</h1>
        <p>Instituto de Matemática e Estatística</p>
    </div>
</header>
<main class="container">
    <h2>Solicitação registrada</h2>
    <pre>{oficio_escaped}</pre>
</main>
</body>
</html>'''
    return html

def validate(data, aba):
    errors = []
    required_common = ["nome", "nusp", "programa", "email", "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao", "data_nasc", "logradouro", "numero", "bairro", "cep", "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta"]
    if aba == "ALUNOS":
        required_common += ["nivel", "tipo_auxilio"]
    missing = any(not data.get(field) for field in required_common)
    if missing:
        errors.append("Preencha todos os campos")
    
    nusp = data.get("nusp", "")
    if nusp and not nusp.isdigit():
        errors.append("N. USP deve conter apenas números")
    
    agencia = data.get("agencia", "")
    if agencia and not agencia.isdigit():
        errors.append("Número da agência deve conter apenas números")
    
    valor = data.get("valor", "")
    if valor:
        digits = ''.join(ch for ch in valor if ch.isdigit())
        if digits:
            cents = int(digits)
            if cents <= 0:
                errors.append("Valor solicitado deve ser maior que 0")
        else:
            errors.append("Valor solicitado deve ser maior que 0")
    
    email = data.get("email", "")
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("E-mail inválido")
    
    cpf = data.get("cpf", "")
    if cpf and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
        errors.append("CPF deve estar no formato 000.000.000-00")
    
    cep = data.get("cep", "")
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        errors.append("CEP deve estar no formato 00000-000")
    
    data_nasc = data.get("data_nasc", "")
    if data_nasc and not re.match(r"^\d{2}/\d{2}/\d{4}$", data_nasc):
        errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    
    return errors

def gerar_oficio(data, aba):
    nome = data.get("nome", "")
    nusp = data.get("nusp", "")
    email = data.get("email", "")
    programa = data.get("programa", "")
    evento = data.get("evento", "")
    periodo = data.get("periodo", "")
    cidade_evento = data.get("cidade_evento", "")
    estado_evento = data.get("estado_evento", "")
    pais_evento = data.get("pais_evento", "")
    link_evento = data.get("link_evento", "")
    apresentacao = data.get("apresentacao", "")
    valor = data.get("valor", "")
    detalhamento = data.get("detalhamento", "")
    logradouro = data.get("logradouro", "")
    numero = data.get("numero", "")
    complemento = data.get("complemento", "")
    cep = data.get("cep", "")
    bairro = data.get("bairro", "")
    cidade_end = data.get("cidade_end", "")
    estado_end = data.get("estado_end", "")
    data_nasc = data.get("data_nasc", "")
    cpf = data.get("cpf", "")
    rg = data.get("rg", "")
    banco = data.get("banco", "")
    agencia = data.get("agencia", "")
    conta = data.get("conta", "")
    
    if aba == "ALUNOS":
        tipo_auxilio = data.get("tipo_auxilio", "")
        nivel = data.get("nivel", "")
        assunto = f"Solicitação de Auxílio Financeiro - {tipo_auxilio}"
        programa_line = f"{programa} - {nivel}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_line = programa
    
    lines = []
    lines.append(f"Interessada(o): {nome} - {nusp}")
    lines.append(f"E-mail: {email}")
    lines.append(f"Assunto: {assunto}")
    lines.append(f"Programa: {programa_line}")
    lines.append("")
    lines.append(f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {evento}")
    lines.append(f"Período: {periodo}")
    lines.append(f"Local: {cidade_evento} - {estado_evento} - {pais_evento}")
    if link_evento:
        lines.append(f"Link do evento: {link_evento}")
    lines.append(f"Apresentação de trabalho: {apresentacao}")
    lines.append(f"Valor solicitado: {valor}")
    lines.append(f"Detalhamento: {detalhamento}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{logradouro}, {numero}")
    if complemento:
        lines.append(f"Complemento: {complemento}")
    lines.append(f"CEP: {cep}")
    lines.append(f"{bairro}, {cidade_end} - {estado_end}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {data_nasc}")
    lines.append(f"CPF: {cpf}")
    lines.append(f"RG / RNM: {rg}")
    lines.append(f"Banco: {banco}")
    lines.append(f"Agência: {agencia}")
    lines.append(f"Conta: {conta}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(lines)

@app.get("/", response_class=HTMLResponse)
async def get_form():
    return HTMLResponse(render_form_page({}, "ALUNOS", []))

@app.post("/", response_class=HTMLResponse)
async def submit_form(request: Request):
    form_data = await request.form()
    data = dict(form_data)
    aba = data.get("aba", "ALUNOS")
    errors = validate(data, aba)
    if errors:
        return HTMLResponse(render_form_page(data, aba, errors))
    oficio = gerar_oficio(data, aba)
    return HTMLResponse(render_confirmation_page(oficio))
