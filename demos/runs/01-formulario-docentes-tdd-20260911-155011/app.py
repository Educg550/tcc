import html as html_lib
import re

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


ALL_FIELDS = [
    "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "link_evento", "valor_solicitado", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "complemento", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

REQUIRED_COMMON = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo_evento",
    "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def esc(s):
    return html_lib.escape(str(s), quote=True)


def default_values():
    return {k: "" for k in ALL_FIELDS}


def extract_values(form, aba):
    return {k: form.get(k, "") for k in ALL_FIELDS}


def parse_money_cents(value):
    digits = re.sub(r"\D", "", value or "")
    if digits == "":
        return None
    return int(digits)


def format_money(cents):
    reais = cents // 100
    centavos = cents % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{centavos:02d}"


def valid_email(email):
    email = email or ""
    if "@" not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local) and bool(domain)


def validate(values, aba):
    errors = []
    required = list(REQUIRED_COMMON)
    if aba == "alunos":
        required += ["nivel", "tipo_auxilio"]
    if any(not (values.get(f, "") or "").strip() for f in required):
        errors.append("Preencha todos os campos")
    if not (values.get("n_usp", "") or "").isdigit():
        errors.append("N. USP deve conter apenas números")
    if not (values.get("agencia", "") or "").isdigit():
        errors.append("Número da agência deve conter apenas números")
    cents = parse_money_cents(values.get("valor_solicitado", ""))
    if cents is None or cents <= 0:
        errors.append("Valor solicitado deve ser maior que 0")
    if not valid_email(values.get("email", "")):
        errors.append("E-mail inválido")
    if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", values.get("cpf", "") or ""):
        errors.append("CPF deve estar no formato 000.000.000-00")
    if not re.match(r"^\d{5}-\d{3}$", values.get("cep", "") or ""):
        errors.append("CEP deve estar no formato 00000-000")
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", values.get("data_nascimento", "") or ""):
        errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    return errors


def build_oficio(values, aba):
    valor_formatado = format_money(parse_money_cents(values["valor_solicitado"]))

    lines = [
        f"Interessada(o): {values['nome_completo']} - {values['n_usp']}",
        f"E-mail: {values['email']}",
    ]
    if aba == "alunos":
        lines.append(f"Assunto: Solicitação de Auxílio Financeiro - {values['tipo_auxilio']}")
        lines.append(f"Programa: {values['programa']} - {values['nivel']}")
    else:
        lines.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        lines.append(f"Programa: {values['programa']}")
    lines.append("")
    lines.append(f"A CCP-{values['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {values['nome_evento']}")
    lines.append(f"Período: {values['periodo_evento']}")
    lines.append(f"Local: {values['cidade_evento']} - {values['estado_evento']} - {values['pais_evento']}")
    if (values["link_evento"] or "").strip():
        lines.append(f"Link do evento: {values['link_evento']}")
    lines.append(f"Apresentação de trabalho: {values['apresentacao']}")
    lines.append(f"Valor solicitado: {valor_formatado}")
    lines.append(f"Detalhamento: {values['detalhamento']}")
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(f"{values['logradouro']}, {values['numero']}")
    if (values["complemento"] or "").strip():
        lines.append(f"Complemento: {values['complemento']}")
    lines.append(f"CEP: {values['cep']}")
    lines.append(f"{values['bairro']}, {values['cidade']} - {values['estado']}")
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {values['data_nascimento']}")
    lines.append(f"CPF: {values['cpf']}")
    lines.append(f"RG / RNM: {values['rg']}")
    lines.append(f"Banco: {values['banco']}")
    lines.append(f"Agência: {values['agencia']}")
    lines.append(f"Conta: {values['conta']}")
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return "\n".join(lines)


HEADER_HTML = """
<header class="site-header">
  <div class="header-logo">
    <img src="/assets/usp-logo.png" alt="Universidade de São Paulo">
  </div>
  <div class="header-text">
    <h1 class="uni-name">Universidade de São Paulo</h1>
    <p class="program-name">Pós-Graduação do Instituto de Matemática e Estatística</p>
  </div>
</header>
"""

CSS = """
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: 'Open Sans', Arial, sans-serif;
  color: #222;
  background: #f4f8f9;
}
.site-header {
  display: flex;
  align-items: center;
  gap: 24px;
  background: #1094ab;
  color: #fff;
  padding: 32px;
}
.header-logo img {
  height: 64px;
  padding: 16px;
}
.uni-name {
  margin: 0;
  font-size: 1.6em;
}
.program-name {
  margin: 4px 0 0;
  font-size: 0.95em;
  color: #e6f7fa;
}
main {
  max-width: 900px;
  margin: 32px auto;
  padding: 0 24px 48px;
}
.tabs {
  display: flex;
  border-bottom: 2px solid #64c4d2;
  margin-bottom: 24px;
}
.tab-button {
  flex: 1;
  padding: 14px;
  border: none;
  background: #e0f2f4;
  color: #1094ab;
  font-weight: bold;
  cursor: pointer;
  font-size: 1em;
}
.tab-button.active {
  background: #1094ab;
  color: #fff;
}
.tab-content { display: none; }
.tab-content.active { display: block; }
form {
  background: #fff;
  padding: 24px;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
h2 {
  color: #1094ab;
  border-bottom: 2px solid #fcb421;
  padding-bottom: 6px;
  margin-top: 32px;
}
.field {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}
label {
  font-weight: bold;
  margin-bottom: 6px;
  font-size: 0.9em;
}
input, select, textarea {
  padding: 10px;
  border: 1px solid #bbb;
  border-radius: 4px;
  font-family: inherit;
  font-size: 1em;
}
button[type="submit"] {
  background: #fcb421;
  border: none;
  padding: 14px 28px;
  font-weight: bold;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 16px;
}
.errors {
  background: #fdecea;
  border: 1px solid #d33;
  color: #a00;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 4px;
}
.errors p { margin: 4px 0; }
.oficio {
  background: #fff;
  padding: 24px;
  border-radius: 6px;
  white-space: pre-wrap;
  font-family: 'Open Sans', Arial, sans-serif;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
"""

JS = """
document.querySelectorAll('.tab-button').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var target = btn.getAttribute('data-tab');
    document.querySelectorAll('.tab-button').forEach(function(b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
    btn.classList.add('active');
    document.getElementById('tab-' + target).classList.add('active');
  });
});

function applyMask(digits, mask) {
  var result = '';
  var di = 0;
  for (var i = 0; i < mask.length && di < digits.length; i++) {
    if (mask[i] === '0') {
      result += digits[di];
      di++;
    } else {
      result += mask[i];
    }
  }
  return result;
}

function maskOnBlur(selector, mask) {
  document.querySelectorAll(selector).forEach(function(el) {
    el.addEventListener('blur', function() {
      var digits = el.value.replace(/\\D/g, '');
      if (digits.length === 0) { return; }
      el.value = applyMask(digits, mask);
    });
  });
}

maskOnBlur('.cpf-field', '000.000.000-00');
maskOnBlur('.cep-field', '00000-000');
maskOnBlur('.date-field', '00/00/0000');

document.querySelectorAll('.money-field').forEach(function(el) {
  el.addEventListener('blur', function() {
    var digits = el.value.replace(/\\D/g, '');
    if (digits.length === 0) { return; }
    var cents = parseInt(digits, 10);
    var reais = Math.floor(cents / 100);
    var centavos = cents % 100;
    var reaisStr = String(reais).replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.');
    var centavosStr = String(centavos).padStart(2, '0');
    el.value = 'R$ ' + reaisStr + ',' + centavosStr;
  });
});
"""


def render_form(aba, values, errors):
    def input_field(label, name, type_="text", placeholder="", extra_class=""):
        val = esc(values.get(name, ""))
        cls = f' class="{extra_class}"' if extra_class else ""
        return (
            f'<div class="field"><label>{label}</label>'
            f'<input type="{type_}" name="{name}" placeholder="{placeholder}" '
            f'value="{val}"{cls}></div>'
        )

    def textarea_field(label, name, placeholder=""):
        val = esc(values.get(name, ""))
        return (
            f'<div class="field"><label>{label}</label>'
            f'<textarea name="{name}" placeholder="{placeholder}" rows="4">{val}</textarea></div>'
        )

    def select_field(label, name, options):
        selected_value = values.get(name, "")
        opts = "".join(
            f'<option value="{esc(opt)}"{" selected" if opt == selected_value else ""}>{opt}</option>'
            for opt in options
        )
        return (
            f'<div class="field"><label>{label}</label>'
            f'<select name="{name}">{opts}</select></div>'
        )

    errors_html = ""
    if errors:
        items = "".join(f'<p class="error">{esc(e)}</p>' for e in errors)
        errors_html = f'<div class="errors">{items}</div>'

    solicitante_fields = [
        input_field("NOME COMPLETO - SEM ABREVIAR", "nome_completo", placeholder="Maria da Silva Santos"),
        input_field("N. USP", "n_usp", placeholder="9876543"),
        input_field("PROGRAMA", "programa", placeholder="Ciência da Computação"),
    ]
    if aba == "alunos":
        solicitante_fields.append(select_field("NÍVEL", "nivel", ["Mestrado", "Doutorado"]))
        solicitante_fields.append(select_field(
            "TIPO DE AUXÍLIO", "tipo_auxilio",
            ["Participação em evento", "Banca de exame ou defesa", "Outro"],
        ))
    solicitante_fields += [
        input_field("E-MAIL", "email", type_="email", placeholder="maria.silva@usp.br"),
        input_field("NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "nome_evento", placeholder="Congresso Brasileiro de Computação"),
        input_field("PERÍODO DO EVENTO, EXAME OU DEFESA", "periodo_evento", placeholder="10/03/2024 a 15/03/2024"),
        input_field("CIDADE DO EVENTO, EXAME OU DEFESA", "cidade_evento", placeholder="Fortaleza"),
        input_field("ESTADO DO EVENTO, EXAME OU DEFESA", "estado_evento", placeholder="CE"),
        input_field("PAÍS DO EVENTO, EXAME OU DEFESA", "pais_evento", placeholder="Brasil"),
        input_field("LINK DO EVENTO, EXAME OU DEFESA", "link_evento", placeholder="https://evento.exemplo.br"),
        input_field("VALOR SOLICITADO (R$)", "valor_solicitado", placeholder="R$ 1.500,00", extra_class="money-field"),
        textarea_field("DETALHAMENTO DO PEDIDO", "detalhamento", placeholder="Descreva o pedido de auxílio"),
        select_field(
            "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "apresentacao",
            ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"],
        ),
    ]

    endereco_fields = [
        input_field("DATA DE NASCIMENTO", "data_nascimento", placeholder="01/02/1980", extra_class="date-field"),
        input_field("LOGRADOURO", "logradouro", placeholder="Rua das Flores"),
        input_field("NÚMERO", "numero", placeholder="123"),
        input_field("COMPLEMENTO", "complemento", placeholder="Apto 45"),
        input_field("BAIRRO", "bairro", placeholder="Butantã"),
        input_field("CEP", "cep", placeholder="05508-090", extra_class="cep-field"),
        input_field("CIDADE", "cidade", placeholder="São Paulo"),
        input_field("ESTADO", "estado", placeholder="SP"),
    ]

    pagamento_fields = [
        input_field("CPF (SEPARADOS POR PONTOS E TRAÇO)", "cpf", placeholder="123.456.789-01", extra_class="cpf-field"),
        input_field("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "rg", placeholder="12.345.678-9"),
        input_field("NOME DO BANCO", "banco", placeholder="Banco do Brasil"),
        input_field("NÚMERO DA AGÊNCIA", "agencia", placeholder="1234"),
        input_field("NÚMERO DA CONTA", "conta", placeholder="56789-0"),
    ]

    return (
        f'<form action="/{aba}" method="post">'
        f"{errors_html}"
        f'<h2>SOLICITANTE E EVENTO</h2>{"".join(solicitante_fields)}'
        f'<h2>ENDEREÇO DO SOLICITANTE</h2>{"".join(endereco_fields)}'
        f'<h2>INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</h2>{"".join(pagamento_fields)}'
        f'<button type="submit">Enviar solicitação</button>'
        f'</form>'
    )


def render_page(active_tab="alunos", errors_alunos=None, errors_docentes=None,
                 values_alunos=None, values_docentes=None):
    errors_alunos = errors_alunos or []
    errors_docentes = errors_docentes or []
    values_alunos = values_alunos or default_values()
    values_docentes = values_docentes or default_values()

    form_alunos = render_form("alunos", values_alunos, errors_alunos)
    form_docentes = render_form("docentes", values_docentes, errors_docentes)

    active_alunos = "active" if active_tab == "alunos" else ""
    active_docentes = "active" if active_tab == "docentes" else ""

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Solicitação de Auxílio Financeiro - IME-USP</title>
<style>{CSS}</style>
</head>
<body>
{HEADER_HTML}
<main>
<div class="tabs">
<button type="button" class="tab-button {active_alunos}" data-tab="alunos">ALUNOS</button>
<button type="button" class="tab-button {active_docentes}" data-tab="docentes">DOCENTES</button>
</div>
<div id="tab-alunos" class="tab-content {active_alunos}">
{form_alunos}
</div>
<div id="tab-docentes" class="tab-content {active_docentes}">
{form_docentes}
</div>
</main>
<script>{JS}</script>
</body>
</html>"""


def render_confirmation(oficio_text):
    escaped = esc(oficio_text)
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Solicitação registrada - IME-USP</title>
<style>{CSS}</style>
</head>
<body>
{HEADER_HTML}
<main>
<h1>Solicitação registrada</h1>
<pre class="oficio">{escaped}</pre>
</main>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return render_page()


@app.post("/alunos", response_class=HTMLResponse)
async def post_alunos(request: Request):
    form = await request.form()
    values = extract_values(form, "alunos")
    errors = validate(values, "alunos")
    if errors:
        return render_page(active_tab="alunos", errors_alunos=errors, values_alunos=values)
    return render_confirmation(build_oficio(values, "alunos"))


@app.post("/docentes", response_class=HTMLResponse)
async def post_docentes(request: Request):
    form = await request.form()
    values = extract_values(form, "docentes")
    errors = validate(values, "docentes")
    if errors:
        return render_page(active_tab="docentes", errors_docentes=errors, values_docentes=values)
    return render_confirmation(build_oficio(values, "docentes"))
