from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import re
import datetime

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# -------------------- helpers --------------------

FIELD_ALIASES = {
    "nome": ["NOME COMPLETO - SEM ABREVIAR", "nome"],
    "nusp": ["N. USP", "n_usp"],
    "programa": ["PROGRAMA", "programa"],
    "nivel": ["NÍVEL", "NÍMEL", "nivel"],
    "tipo_auxilio": ["TIPO DE AUXÍLIO", "tipo_auxilio"],
    "email": ["E-MAIL", "email"],
    "nome_evento": ["NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "nome_evento"],
    "periodo": ["PERÍODO DO EVENTO, EXAME OU DEFESA", "periodo"],
    "cidade_evento": ["CIDADE DO EVENTO, EXAME OU DEFESA", "cidade_evento"],
    "estado_evento": ["ESTADO DO EVENTO, EXAME OU DEFESA", "estado_evento"],
    "pais_evento": ["PAÍS DO EVENTO, EXAME OU DEFESA", "pais_evento"],
    "link_evento": ["LINK DO EVENTO, EXAME OU DEFESA", "link_evento"],
    "valor_solicitado": ["VALOR SOLICITADO (R$)", "valor_solicitado"],
    "detalhamento": ["DETALHAMENTO DO PEDIDO", "detalhamento"],
    "apresentacao": ["IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "apresentacao"],
    "data_nascimento": ["DATA DE NASCIMENTO", "data_nascimento"],
    "logradouro": ["LOGRADOURO", "logradouro"],
    "numero": ["NÚMERO", "numero"],
    "complemento": ["COMPLEMENTO", "complemento"],
    "bairro": ["BAIRRO", "bairro"],
    "cep": ["CEP", "cep"],
    "cidade_end": ["CIDADE", "cidade_end"],
    "estado_end": ["ESTADO", "estado_end"],
    "cpf": ["CPF (SEPARADOS POR PONTOS E TRAÇO)", "cpf"],
    "rg": ["RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "rg"],
    "banco": ["NOME DO BANCO", "banco"],
    "agencia": ["NÚMERO DA AGÊNCIA", "agencia"],
    "conta": ["NÚMERO DA CONTA", "conta"],
}

def get_field(form, key):
    for alias in FIELD_ALIASES.get(key, [key]):
        val = form.get(alias)
        if val is not None:
            return val
    return ""

def format_currency(digits):
    if not digits:
        return ""
    try:
        n = int(digits)
    except ValueError:
        return ""
    reais = n // 100
    cents = n % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{cents:02d}"

def format_cpf(digits):
    if len(digits) != 11:
        return digits
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

def format_cep(digits):
    if len(digits) != 8:
        return digits
    return f"{digits[:5]}-{digits[5:]}"

def format_date(digits):
    if len(digits) != 8:
        return digits
    return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"

# -------------------- validation --------------------

def validate(form, tab):
    errors = []
    data = {}
    for field in FIELD_ALIASES.keys():
        data[field] = get_field(form, field).strip()

    mandatory = [
        "nome", "nusp", "programa", "email", "nome_evento",
        "periodo", "cidade_evento", "estado_evento", "pais_evento",
        "valor_solicitado", "detalhamento", "apresentacao",
        "data_nascimento", "logradouro", "numero", "bairro",
        "cep", "cidade_end", "estado_end", "cpf", "rg",
        "banco", "agencia", "conta"
    ]
    if tab == "alunos":
        mandatory += ["nivel", "tipo_auxilio"]

    if any(not data[f] for f in mandatory):
        errors.append("Preencha todos os campos")

    if data["nusp"] and not data["nusp"].isdigit():
        errors.append("N. USP deve conter apenas números")

    if data["agencia"] and not data["agencia"].isdigit():
        errors.append("Número da agência deve conter apenas números")

    if data["valor_solicitado"] and not (data["valor_solicitado"].isdigit() and int(data["valor_solicitado"]) > 0):
        errors.append("Valor solicitado deve ser maior que 0")

    if data["email"]:
        if "@" not in data["email"] or not re.search(r'\.[a-zA-Z]', data["email"].split('@')[-1]):
            errors.append("E-mail inválido")

    cpf_digits = re.sub(r'\D', '', data["cpf"])
    if data["cpf"] and len(cpf_digits) != 11:
        errors.append("CPF deve estar no formato 000.000.000-00")

    cep_digits = re.sub(r'\D', '', data["cep"])
    if data["cep"] and len(cep_digits) != 8:
        errors.append("CEP deve estar no formato 00000-000")

    data_nasc_digits = re.sub(r'\D', '', data["data_nascimento"])
    if data["data_nascimento"]:
        if len(data_nasc_digits) == 8:
            try:
                day, month, year = int(data_nasc_digits[:2]), int(data_nasc_digits[2:4]), int(data_nasc_digits[4:])
                datetime.datetime(year, month, day)
            except ValueError:
                errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    # prepare formatted values (will be used only if no errors, but we prepare anyway)
    data["valor_formatted"] = format_currency(data["valor_solicitado"]) if data["valor_solicitado"] else ""
    data["cpf_formatted"] = format_cpf(cpf_digits) if cpf_digits else ""
    data["cep_formatted"] = format_cep(cep_digits) if cep_digits else ""
    data["data_formatted"] = format_date(data_nasc_digits) if data_nasc_digits else ""

    return errors, data

# -------------------- template rendering --------------------

COMMON_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Open Sans', sans-serif; background: #f9f9f9; color: #333; }
.header { background: white; border-bottom: 3px solid #1094ab; padding: 20px; display: flex; align-items: center; }
.logo { height: 60px; margin-right: 20px; }
.header-text h1 { font-size: 1.5em; color: #1094ab; font-weight: 700; }
.header-text p { font-size: 0.9em; color: #666; }
.container { max-width: 900px; margin: 20px auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
.tabs { display: flex; border-bottom: 2px solid #1094ab; margin-bottom: 20px; }
.tab { padding: 10px 20px; cursor: pointer; background: #e0e0e0; border: none; font-weight: bold; color: #333; transition: background 0.3s; }
.tab.active { background: #1094ab; color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.9em; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 1em; }
.form-group textarea { resize: vertical; min-height: 80px; }
button[type="submit"] { background: #1094ab; color: white; padding: 12px 24px; border: none; border-radius: 4px; font-size: 1em; cursor: pointer; margin-top: 20px; }
button[type="submit"]:hover { background: #0d7b8f; }
.error-box { background: #ffe6e6; border: 1px solid #d9534f; padding: 10px; margin-bottom: 20px; border-radius: 4px; color: #a94442; white-space: pre-line; }
.section-title { border-bottom: 2px solid #1094ab; padding-bottom: 5px; margin: 30px 0 20px 0; color: #1094ab; font-size: 1.2em; }
.hidden { display: none; }
pre { white-space: pre-wrap; font-family: 'Open Sans', sans-serif; font-size: 1em; line-height: 1.5; }
"""

def render_main(active_tab="alunos", errors=None, form_data=None):
    if errors is None:
        errors = []
    if form_data is None:
        form_data = {}

    def val(key):
        return form_data.get(key, "")

    def sel(key, option):
        return "selected" if val(key) == option else ""

    # auto-format fields
    raw_valor = val("valor_solicitado")
    formatted_valor = format_currency(raw_valor) if raw_valor else ""
    raw_cpf = val("cpf")
    cpf_digits_clean = re.sub(r'\D', '', raw_cpf) if raw_cpf else ""
    formatted_cpf = format_cpf(cpf_digits_clean) if cpf_digits_clean else ""
    raw_cep = val("cep")
    cep_digits_clean = re.sub(r'\D', '', raw_cep) if raw_cep else ""
    formatted_cep = format_cep(cep_digits_clean) if cep_digits_clean else ""
    raw_data = val("data_nascimento")
    data_digits_clean = re.sub(r'\D', '', raw_data) if raw_data else ""
    formatted_data = format_date(data_digits_clean) if data_digits_clean else ""

    errors_html = ""
    if errors:
        errors_html = '<div class="error-box">' + "\n".join(errors) + '</div>'

    html = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Solicitação de Auxílio Financeiro - IME-USP</title>
    <style>
        {COMMON_CSS}
    </style>
</head>
<body>
    <div class="header">
        <img src="/assets/usp-logo.png" alt="Logo USP" class="logo">
        <div class="header-text">
            <h1>Universidade de São Paulo</h1>
            <p>Pós-Graduação IME-USP</p>
        </div>
    </div>
    <div class="container">
        <div class="tabs">
            <button class="tab {"active" if active_tab == "alunos" else ""}" id="tab-alunos" onclick="switchTab('alunos')">ALUNOS</button>
            <button class="tab {"active" if active_tab == "docentes" else ""}" id="tab-docentes" onclick="switchTab('docentes')">DOCENTES</button>
        </div>
        <div id="form-alunos" class="tab-content {"active" if active_tab == "alunos" else ""}">
            {errors_html if active_tab == "alunos" else ""}
            <form method="post" action="/enviar/alunos">
                <div class="section-title">SOLICITANTE E EVENTO</div>
                <div class="form-group">
                    <label>NOME COMPLETO - SEM ABREVIAR</label>
                    <input type="text" name="NOME COMPLETO - SEM ABREVIAR" placeholder="Ex: João da Silva" value="{val('nome')}">
                </div>
                <div class="form-group">
                    <label>N. USP</label>
                    <input type="text" name="N. USP" placeholder="12345678" value="{val('nusp')}">
                </div>
                <div class="form-group">
                    <label>PROGRAMA</label>
                    <input type="text" name="PROGRAMA" placeholder="Ex: CCP" value="{val('programa')}">
                </div>
                <div class="form-group">
                    <label>NÍVEL</label>
                    <select name="NÍVEL">
                        <option value="" disabled {"selected" if not val('nivel') else ""}>Selecione</option>
                        <option value="Mestrado" {sel('nivel', 'Mestrado')}>Mestrado</option>
                        <option value="Doutorado" {sel('nivel', 'Doutorado')}>Doutorado</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>TIPO DE AUXÍLIO</label>
                    <select name="TIPO DE AUXÍLIO">
                        <option value="" disabled {"selected" if not val('tipo_auxilio') else ""}>Selecione</option>
                        <option value="Participação em evento" {sel('tipo_auxilio', 'Participação em evento')}>Participação em evento</option>
                        <option value="Banca de exame ou defesa" {sel('tipo_auxilio', 'Banca de exame ou defesa')}>Banca de exame ou defesa</option>
                        <option value="Outro" {sel('tipo_auxilio', 'Outro')}>Outro</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>E-MAIL</label>
                    <input type="email" name="E-MAIL" placeholder="exemplo@usp.br" value="{val('email')}">
                </div>
                <div class="form-group">
                    <label>NOME DO EVENTO / BANCA DE EXAME OU DEFESA</label>
                    <input type="text" name="NOME DO EVENTO / BANCA DE EXAME OU DEFESA" placeholder="Ex: Simpósio Nacional" value="{val('nome_evento')}">
                </div>
                <div class="form-group">
                    <label>PERÍODO DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="PERÍODO DO EVENTO, EXAME OU DEFESA" placeholder="01/06/2025 a 05/06/2025" value="{val('periodo')}">
                </div>
                <div class="form-group">
                    <label>CIDADE DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="CIDADE DO EVENTO, EXAME OU DEFESA" placeholder="São Paulo" value="{val('cidade_evento')}">
                </div>
                <div class="form-group">
                    <label>ESTADO DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="ESTADO DO EVENTO, EXAME OU DEFESA" placeholder="SP" value="{val('estado_evento')}">
                </div>
                <div class="form-group">
                    <label>PAÍS DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="PAÍS DO EVENTO, EXAME OU DEFESA" placeholder="Brasil" value="{val('pais_evento')}">
                </div>
                <div class="form-group">
                    <label>LINK DO EVENTO, EXAME OU DEFESA (opcional)</label>
                    <input type="text" name="LINK DO EVENTO, EXAME OU DEFESA" placeholder="http://evento.br" value="{val('link_evento')}">
                </div>
                <div class="form-group">
                    <label>VALOR SOLICITADO (R$)</label>
                    <input type="text" id="valor_display_alunos" placeholder="1500" value="{formatted_valor}" onblur="formatMoney(this, 'VALOR SOLICITADO (R$)')" onfocus="showRawMoney(this, 'VALOR SOLICITADO (R$)')">
                    <input type="hidden" name="VALOR SOLICITADO (R$)" id="valor_raw_alunos" value="{raw_valor}">
                </div>
                <div class="form-group">
                    <label>DETALHAMENTO DO PEDIDO</label>
                    <textarea name="DETALHAMENTO DO PEDIDO" placeholder="Descreva o detalhamento..." rows="4">{val('detalhamento')}</textarea>
                </div>
                <div class="form-group">
                    <label>IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?</label>
                    <select name="IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?">
                        <option value="" disabled {"selected" if not val('apresentacao') else ""}>Selecione</option>
                        <option value="Pôster" {sel('apresentacao', 'Pôster')}>Pôster</option>
                        <option value="Apresentação oral" {sel('apresentacao', 'Apresentação oral')}>Apresentação oral</option>
                        <option value="Outra" {sel('apresentacao', 'Outra')}>Outra</option>
                        <option value="Não irá apresentar trabalho" {sel('apresentacao', 'Não irá apresentar trabalho')}>Não irá apresentar trabalho</option>
                    </select>
                </div>

                <div class="section-title">ENDEREÇO DO SOLICITANTE</div>
                <div class="form-group">
                    <label>DATA DE NASCIMENTO</label>
                    <input type="text" id="data_display_alunos" placeholder="01021980" value="{formatted_data}" onblur="formatDate(this, 'DATA DE NASCIMENTO')" onfocus="showRawDate(this, 'DATA DE NASCIMENTO')">
                    <input type="hidden" name="DATA DE NASCIMENTO" id="data_raw_alunos" value="{raw_data}">
                </div>
                <div class="form-group">
                    <label>LOGRADOURO</label>
                    <input type="text" name="LOGRADOURO" placeholder="Rua das Flores" value="{val('logradouro')}">
                </div>
                <div class="form-group">
                    <label>NÚMERO</label>
                    <input type="text" name="NÚMERO" placeholder="100" value="{val('numero')}">
                </div>
                <div class="form-group">
                    <label>COMPLEMENTO (opcional)</label>
                    <input type="text" name="COMPLEMENTO" placeholder="Apto 42" value="{val('complemento')}">
                </div>
                <div class="form-group">
                    <label>BAIRRO</label>
                    <input type="text" name="BAIRRO" placeholder="Centro" value="{val('bairro')}">
                </div>
                <div class="form-group">
                    <label>CEP</label>
                    <input type="text" id="cep_display_alunos" placeholder="05508-090" value="{formatted_cep}" onblur="formatCep(this, 'CEP')" onfocus="showRawCep(this, 'CEP')">
                    <input type="hidden" name="CEP" id="cep_raw_alunos" value="{raw_cep}">
                </div>
                <div class="form-group">
                    <label>CIDADE</label>
                    <input type="text" name="CIDADE" placeholder="São Paulo" value="{val('cidade_end')}">
                </div>
                <div class="form-group">
                    <label>ESTADO</label>
                    <input type="text" name="ESTADO" placeholder="SP" value="{val('estado_end')}">
                </div>

                <div class="section-title">INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</div>
                <div class="form-group">
                    <label>CPF (SEPARADOS POR PONTOS E TRAÇO)</label>
                    <input type="text" id="cpf_display_alunos" placeholder="123.456.789-01" value="{formatted_cpf}" onblur="formatCpf(this, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')" onfocus="showRawCpf(this, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')">
                    <input type="hidden" name="CPF (SEPARADOS POR PONTOS E TRAÇO)" id="cpf_raw_alunos" value="{raw_cpf}">
                </div>
                <div class="form-group">
                    <label>RG / RNM (SEPARADOS POR PONTOS E TRAÇO)</label>
                    <input type="text" name="RG / RNM (SEPARADOS POR PONTOS E TRAÇO)" placeholder="12.345.678-9" value="{val('rg')}">
                </div>
                <div class="form-group">
                    <label>NOME DO BANCO</label>
                    <input type="text" name="NOME DO BANCO" placeholder="Banco do Brasil" value="{val('banco')}">
                </div>
                <div class="form-group">
                    <label>NÚMERO DA AGÊNCIA</label>
                    <input type="text" name="NÚMERO DA AGÊNCIA" placeholder="1234" value="{val('agencia')}">
                </div>
                <div class="form-group">
                    <label>NÚMERO DA CONTA</label>
                    <input type="text" name="NÚMERO DA CONTA" placeholder="12345-6" value="{val('conta')}">
                </div>
                <button type="submit">Enviar solicitação</button>
            </form>
        </div>

        <div id="form-docentes" class="tab-content {"active" if active_tab == "docentes" else ""}">
            {errors_html if active_tab == "docentes" else ""}
            <form method="post" action="/enviar/docentes">
                <div class="section-title">SOLICITANTE E EVENTO</div>
                <div class="form-group">
                    <label>NOME COMPLETO - SEM ABREVIAR</label>
                    <input type="text" name="NOME COMPLETO - SEM ABREVIAR" placeholder="Ex: Maria Souza" value="{val('nome')}">
                </div>
                <div class="form-group">
                    <label>N. USP</label>
                    <input type="text" name="N. USP" placeholder="87654321" value="{val('nusp')}">
                </div>
                <div class="form-group">
                    <label>PROGRAMA</label>
                    <input type="text" name="PROGRAMA" placeholder="Ex: CCP" value="{val('programa')}">
                </div>
                <div class="form-group">
                    <label>E-MAIL</label>
                    <input type="email" name="E-MAIL" placeholder="exemplo@usp.br" value="{val('email')}">
                </div>
                <div class="form-group">
                    <label>NOME DO EVENTO / BANCA DE EXAME OU DEFESA</label>
                    <input type="text" name="NOME DO EVENTO / BANCA DE EXAME OU DEFESA" placeholder="Congresso Internacional" value="{val('nome_evento')}">
                </div>
                <div class="form-group">
                    <label>PERÍODO DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="PERÍODO DO EVENTO, EXAME OU DEFESA" placeholder="20/07/2025 a 25/07/2025" value="{val('periodo')}">
                </div>
                <div class="form-group">
                    <label>CIDADE DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="CIDADE DO EVENTO, EXAME OU DEFESA" placeholder="Rio de Janeiro" value="{val('cidade_evento')}">
                </div>
                <div class="form-group">
                    <label>ESTADO DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="ESTADO DO EVENTO, EXAME OU DEFESA" placeholder="RJ" value="{val('estado_evento')}">
                </div>
                <div class="form-group">
                    <label>PAÍS DO EVENTO, EXAME OU DEFESA</label>
                    <input type="text" name="PAÍS DO EVENTO, EXAME OU DEFESA" placeholder="Brasil" value="{val('pais_evento')}">
                </div>
                <div class="form-group">
                    <label>LINK DO EVENTO, EXAME OU DEFESA (opcional)</label>
                    <input type="text" name="LINK DO EVENTO, EXAME OU DEFESA" placeholder="http://evento.br" value="{val('link_evento')}">
                </div>
                <div class="form-group">
                    <label>VALOR SOLICITADO (R$)</label>
                    <input type="text" id="valor_display_docentes" placeholder="250000" value="{formatted_valor}" onblur="formatMoney(this, 'VALOR SOLICITADO (R$)')" onfocus="showRawMoney(this, 'VALOR SOLICITADO (R$)')">
                    <input type="hidden" name="VALOR SOLICITADO (R$)" id="valor_raw_docentes" value="{raw_valor}">
                </div>
                <div class="form-group">
                    <label>DETALHAMENTO DO PEDIDO</label>
                    <textarea name="DETALHAMENTO DO PEDIDO" placeholder="Descreva o detalhamento..." rows="4">{val('detalhamento')}</textarea>
                </div>
                <div class="form-group">
                    <label>IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?</label>
                    <select name="IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?">
                        <option value="" disabled {"selected" if not val('apresentacao') else ""}>Selecione</option>
                        <option value="Pôster" {sel('apresentacao', 'Pôster')}>Pôster</option>
                        <option value="Apresentação oral" {sel('apresentacao', 'Apresentação oral')}>Apresentação oral</option>
                        <option value="Outra" {sel('apresentacao', 'Outra')}>Outra</option>
                        <option value="Não irá apresentar trabalho" {sel('apresentacao', 'Não irá apresentar trabalho')}>Não irá apresentar trabalho</option>
                    </select>
                </div>

                <div class="section-title">ENDEREÇO DO SOLICITANTE</div>
                <div class="form-group">
                    <label>DATA DE NASCIMENTO</label>
                    <input type="text" id="data_display_docentes" placeholder="15051978" value="{formatted_data}" onblur="formatDate(this, 'DATA DE NASCIMENTO')" onfocus="showRawDate(this, 'DATA DE NASCIMENTO')">
                    <input type="hidden" name="DATA DE NASCIMENTO" id="data_raw_docentes" value="{raw_data}">
                </div>
                <div class="form-group">
                    <label>LOGRADOURO</label>
                    <input type="text" name="LOGRADOURO" placeholder="Av. Paulista" value="{val('logradouro')}">
                </div>
                <div class="form-group">
                    <label>NÚMERO</label>
                    <input type="text" name="NÚMERO" placeholder="1000" value="{val('numero')}">
                </div>
                <div class="form-group">
                    <label>COMPLEMENTO (opcional)</label>
                    <input type="text" name="COMPLEMENTO" placeholder="Sala 101" value="{val('complemento')}">
                </div>
                <div class="form-group">
                    <label>BAIRRO</label>
                    <input type="text" name="BAIRRO" placeholder="Bela Vista" value="{val('bairro')}">
                </div>
                <div class="form-group">
                    <label>CEP</label>
                    <input type="text" id="cep_display_docentes" placeholder="01310-100" value="{formatted_cep}" onblur="formatCep(this, 'CEP')" onfocus="showRawCep(this, 'CEP')">
                    <input type="hidden" name="CEP" id="cep_raw_docentes" value="{raw_cep}">
                </div>
                <div class="form-group">
                    <label>CIDADE</label>
                    <input type="text" name="CIDADE" placeholder="São Paulo" value="{val('cidade_end')}">
                </div>
                <div class="form-group">
                    <label>ESTADO</label>
                    <input type="text" name="ESTADO" placeholder="SP" value="{val('estado_end')}">
                </div>

                <div class="section-title">INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</div>
                <div class="form-group">
                    <label>CPF (SEPARADOS POR PONTOS E TRAÇO)</label>
                    <input type="text" id="cpf_display_docentes" placeholder="987.654.321-09" value="{formatted_cpf}" onblur="formatCpf(this, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')" onfocus="showRawCpf(this, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')">
                    <input type="hidden" name="CPF (SEPARADOS POR PONTOS E TRAÇO)" id="cpf_raw_docentes" value="{raw_cpf}">
                </div>
                <div class="form-group">
                    <label>RG / RNM (SEPARADOS POR PONTOS E TRAÇO)</label>
                    <input type="text" name="RG / RNM (SEPARADOS POR PONTOS E TRAÇO)" placeholder="987654321" value="{val('rg')}">
                </div>
                <div class="form-group">
                    <label>NOME DO BANCO</label>
                    <input type="text" name="NOME DO BANCO" placeholder="Itaú" value="{val('banco')}">
                </div>
                <div class="form-group">
                    <label>NÚMERO DA AGÊNCIA</label>
                    <input type="text" name="NÚMERO DA AGÊNCIA" placeholder="4321" value="{val('agencia')}">
                </div>
                <div class="form-group">
                    <label>NÚMERO DA CONTA</label>
                    <input type="text" name="NÚMERO DA CONTA" placeholder="98765-0" value="{val('conta')}">
                </div>
                <button type="submit">Enviar solicitação</button>
            </form>
        </div>
    </div>

    <script>
        function switchTab(tab) {{
            document.getElementById('tab-alunos').classList.toggle('active', tab === 'alunos');
            document.getElementById('tab-docentes').classList.toggle('active', tab === 'docentes');
            document.getElementById('form-alunos').classList.toggle('active', tab === 'alunos');
            document.getElementById('form-docentes').classList.toggle('active', tab === 'docentes');
        }}

        function formatMoney(input, hiddenName) {{
            var raw = input.value.replace(/\D/g, '');
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden') {{
                hidden.value = raw;
            }}
            if (raw) {{
                var n = parseInt(raw, 10);
                var reais = Math.floor(n / 100);
                var cents = n % 100;
                var formatted = 'R$ ' + reais.toString().replace(/\B(?=(\d{{3}})+(?!\d))/g, '.') + ',' + String(cents).padStart(2, '0');
                input.value = formatted;
            }} else {{
                input.value = '';
                if (hidden) hidden.value = '';
            }}
        }}

        function showRawMoney(input, hiddenName) {{
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden' && hidden.value) {{
                input.value = hidden.value;
            }}
        }}

        function formatCpf(input, hiddenName) {{
            var raw = input.value.replace(/\D/g, '');
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden') {{
                hidden.value = raw;
            }}
            if (raw.length === 11) {{
                input.value = raw.slice(0,3) + '.' + raw.slice(3,6) + '.' + raw.slice(6,9) + '-' + raw.slice(9);
            }} else if (raw) {{
                input.value = raw;
            }} else {{
                input.value = '';
                if (hidden) hidden.value = '';
            }}
        }}

        function showRawCpf(input, hiddenName) {{
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden' && hidden.value) {{
                input.value = hidden.value;
            }}
        }}

        function formatCep(input, hiddenName) {{
            var raw = input.value.replace(/\D/g, '');
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden') {{
                hidden.value = raw;
            }}
            if (raw.length === 8) {{
                input.value = raw.slice(0,5) + '-' + raw.slice(5);
            }} else if (raw) {{
                input.value = raw;
            }} else {{
                input.value = '';
                if (hidden) hidden.value = '';
            }}
        }}

        function showRawCep(input, hiddenName) {{
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden' && hidden.value) {{
                input.value = hidden.value;
            }}
        }}

        function formatDate(input, hiddenName) {{
            var raw = input.value.replace(/\D/g, '');
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden') {{
                hidden.value = raw;
            }}
            if (raw.length === 8) {{
                input.value = raw.slice(0,2) + '/' + raw.slice(2,4) + '/' + raw.slice(4);
            }} else if (raw) {{
                input.value = raw;
            }} else {{
                input.value = '';
                if (hidden) hidden.value = '';
            }}
        }}

        function showRawDate(input, hiddenName) {{
            var hidden = input.nextElementSibling;
            if (hidden && hidden.type === 'hidden' && hidden.value) {{
                input.value = hidden.value;
            }}
        }}
    </script>
</body>
</html>
"""
    return html

def render_oficio(data, tab):
    nome = data.get("nome", "")
    nusp = data.get("nusp", "")
    email = data.get("email", "")
    programa = data.get("programa", "")
    if tab == "alunos":
        nivel = data.get("nivel", "")
        tipo_auxilio = data.get("tipo_auxilio", "")
        assunto = f"Solicitação de Auxílio Financeiro - {tipo_auxilio}"
    else:
        nivel = ""
        tipo_auxilio = ""
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"

    nome_evento = data.get("nome_evento", "")
    periodo = data.get("periodo", "")
    cidade_evento = data.get("cidade_evento", "")
    estado_evento = data.get("estado_evento", "")
    pais_evento = data.get("pais_evento", "")
    link_evento = data.get("link_evento", "")
    apresentacao = data.get("apresentacao", "")
    valor = data.get("valor_formatted", "")
    detalhamento = data.get("detalhamento", "")
    logradouro = data.get("logradouro", "")
    numero = data.get("numero", "")
    complemento = data.get("complemento", "")
    bairro = data.get("bairro", "")
    cep = data.get("cep_formatted", "")
    cidade_end = data.get("cidade_end", "")
    estado_end = data.get("estado_end", "")
    cpf = data.get("cpf_formatted", "")
    rg = data.get("rg", "")
    banco = data.get("banco", "")
    agencia = data.get("agencia", "")
    conta = data.get("conta", "")
    data_nasc = data.get("data_formatted", "")

    lines = []
    lines.append(f"Interessada(o): {nome} - {nusp}")
    lines.append(f"E-mail: {email}")
    lines.append(f"Assunto: {assunto}")
    lines.append(f"Programa: {programa}" + (f" - {nivel}" if tab == "alunos" else ""))
    lines.append("")
    lines.append(f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append(f"interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {nome_evento}")
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

    oficio_text = "\n".join(lines)

    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Solicitação registrada</title>
    <style>
        {COMMON_CSS}
        pre {{ white-space: pre-wrap; font-family: 'Open Sans', sans-serif; }}
    </style>
</head>
<body>
    <div class="header">
        <img src="/assets/usp-logo.png" alt="Logo USP" class="logo">
        <div class="header-text">
            <h1>Universidade de São Paulo</h1>
            <p>Pós-Graduação IME-USP</p>
        </div>
    </div>
    <div class="container">
        <h2>Solicitação registrada</h2>
        <pre>{oficio_text}</pre>
    </div>
</body>
</html>
"""

# -------------------- routes --------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    return render_main()

@app.post("/enviar/alunos", response_class=HTMLResponse)
async def enviar_alunos(request: Request):
    form = await request.form()
    errors, data = validate(form, "alunos")
    if errors:
        return render_main(active_tab="alunos", errors=errors, form_data=data)
    return render_oficio(data, "alunos")

@app.post("/enviar/docentes", response_class=HTMLResponse)
async def enviar_docentes(request: Request):
    form = await request.form()
    errors, data = validate(form, "docentes")
    if errors:
        return render_main(active_tab="docentes", errors=errors, form_data=data)
    return render_oficio(data, "docentes")
