import re
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
import html as html_module

app = Starlette(debug=True)

# -----------------------------------
# Templates
# -----------------------------------

BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Solicitacao de Auxilio Financeiro - IME-USP</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Arial, sans-serif; color: #333; background: #f9f9f9; }}
.header {{ background: #00507c; color: #fff; padding: 20px; text-align: center; }}
.header img {{ max-height: 60px; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
.tabs {{ display: flex; border-bottom: 2px solid #00507c; margin-bottom: 20px; }}
.tab {{ flex: 1; padding: 12px; text-align: center; cursor: pointer; font-weight: bold; background: #e0e0e0; color: #333; border: 1px solid #ccc; border-bottom: none; transition: background 0.2s; }}
.tab.active {{ background: #00507c; color: #fff; border-color: #00507c; }}
.form {{ display: none; }}
.form.active {{ display: block; }}
.errors {{ background: #fdd; color: #a00; padding: 10px; margin-bottom: 15px; border: 1px solid #a00; }}
.bloco {{ margin-bottom: 25px; }}
.bloco h3 {{ color: #00507c; border-bottom: 1px solid #00507c; padding-bottom: 5px; margin-bottom: 15px; }}
label {{ display: block; margin-bottom: 10px; }}
label span {{ display: block; margin-bottom: 4px; font-weight: bold; }}
input, select, textarea {{ width: 100%; padding: 8px; border: 1px solid #aaa; border-radius: 3px; }}
textarea {{ resize: vertical; }}
button {{ background: #00507c; color: #fff; padding: 12px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
button:hover {{ background: #003f5c; }}
pre {{ white-space: pre-wrap; font-family: inherit; }}
</style>
</head>
<body>
<div class="header">
  <h1>Universidade de São Paulo</h1>
  <h2>Instituto de Matemática e Estatística</h2>
</div>
<div class="container">
{conteudo}
</div>
<script>
function showTab(index) {{
    var tabs = document.querySelectorAll('.tab');
    var forms = document.querySelectorAll('.form');
    tabs.forEach(function(t) {{ t.classList.remove('active'); }});
    forms.forEach(function(f) {{ f.classList.remove('active'); }});
    tabs[index].classList.add('active');
    forms[index].classList.add('active');
}}
function formatarCPF(input) {{
    var val = input.value.replace(/\\D/g, '');
    if (val.length > 11) val = val.substring(0, 11);
    if (val.length >= 10) val = val.substring(0, 3) + '.' + val.substring(3, 6) + '.' + val.substring(6, 9) + '-' + val.substring(9);
    else if (val.length >= 7) val = val.substring(0, 3) + '.' + val.substring(3, 6) + '.' + val.substring(6);
    else if (val.length >= 4) val = val.substring(0, 3) + '.' + val.substring(3);
    input.value = val;
}}
function formatarCEP(input) {{
    var val = input.value.replace(/\\D/g, '');
    if (val.length > 8) val = val.substring(0, 8);
    if (val.length >= 6) val = val.substring(0, 5) + '-' + val.substring(5);
    input.value = val;
}}
function formatarData(input) {{
    var val = input.value.replace(/\\D/g, '');
    if (val.length > 8) val = val.substring(0, 8);
    if (val.length >= 5) val = val.substring(0, 2) + '/' + val.substring(2, 4) + '/' + val.substring(4);
    else if (val.length >= 3) val = val.substring(0, 2) + '/' + val.substring(2);
    input.value = val;
}}
function formatarValor(input) {{
    var val = input.value.replace(/\\D/g, '');
    if (val === '') return;
    val = (parseInt(val, 10) || 0) + '';
    while (val.length < 3) val = '0' + val;
    var intPart = val.substring(0, val.length - 2);
    var decPart = val.substring(val.length - 2);
    var formatted = intPart.replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
    input.value = 'R$ ' + formatted + ',' + decPart;
}}
function attachFormatting() {{
    var cpf = document.querySelector('input[name="cpf"]');
    if (cpf) cpf.addEventListener('blur', function() {{ formatarCPF(this); }});
    var cep = document.querySelector('input[name="cep"]');
    if (cep) cep.addEventListener('blur', function() {{ formatarCEP(this); }});
    var data = document.querySelector('input[name="data_de_nascimento"]');
    if (data) data.addEventListener('blur', function() {{ formatarData(this); }});
    var valor = document.querySelector('input[name="valor_solicitado"]');
    if (valor) valor.addEventListener('blur', function() {{ formatarValor(this); }});
}}
document.addEventListener('DOMContentLoaded', function() {{
    attachFormatting();
    var active = document.querySelector('.form.active');
    if (!active) {{
        var forms = document.querySelectorAll('.form');
        if (forms[0]) forms[0].classList.add('active');
        var tabs = document.querySelectorAll('.tab');
        if (tabs[0]) tabs[0].classList.add('active');
    }}
}});
</script>
</body>
</html>'''

OFICIO_ALUNO = '''Interessada(o): {nome} - {nusp}
E-mail: {email}
Assunto: Solicitação de Auxílio Financeiro - {tipo}
Programa: {programa} - {nivel}

A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {evento}
Período: {periodo}
Local: {cidade_evento} - {estado_evento} - {pais_evento}
{link}
Apresentação de trabalho: {apresentacao}
Valor solicitado: {valor}
Detalhamento: {detalhamento}

Endereço da(o) interessada(o)
{endereco}
{complemento}
CEP: {cep}
{bairro}, {cidade} - {estado}

Dados para pagamento
Data de nascimento: {data_nasc}
CPF: {cpf}
RG / RNM: {rg}
Banco: {banco}
Agência: {agencia}
Conta: {conta}

Encaminhe-se ao Serviço Financeiro para providências.'''

OFICIO_DOCENTE = '''Interessada(o): {nome} - {nusp}
E-mail: {email}
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: {programa}

A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {evento}
Período: {periodo}
Local: {cidade_evento} - {estado_evento} - {pais_evento}
{link}
Apresentação de trabalho: {apresentacao}
Valor solicitado: {valor}
Detalhamento: {detalhamento}

Endereço da(o) interessada(o)
{endereco}
{complemento}
CEP: {cep}
{bairro}, {cidade} - {estado}

Dados para pagamento
Data de nascimento: {data_nasc}
CPF: {cpf}
RG / RNM: {rg}
Banco: {banco}
Agência: {agencia}
Conta: {conta}

Encaminhe-se ao Serviço Financeiro para providências.'''

# -----------------------------------
# Helpers de validação
# -----------------------------------

def validar_email(email):
    return '@' in email and '.@' not in email and email.index('@') < len(email) - 1

def validar_cpf(cpf):
    return re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf) is not None

def validar_cep(cep):
    return re.match(r'^\d{5}-\d{3}$', cep) is not None

def validar_data(data):
    return re.match(r'^\d{2}/\d{2}/\d{4}$', data) is not None

def validar_valor(valor_str):
    # Remove formatação e tenta interpretar como centavos
    if not valor_str.startswith('R$ '):
        return False
    valor_str = valor_str[3:]
    cnt = 0
    digits = ''
    for c in valor_str:
        if c.isdigit():
            digits += c
            cnt += 1
        elif c in '.':
            continue  # separador de milhar
        elif c == ',':
            continue  # decimal já no lado dos centavos
        else:
            return False
    if not digits:
        return False
    total = int(digits)
    return total > 0

# -----------------------------------
# Função que monta o HTML do conteúdo
# -----------------------------------

def render_page(active_tab, erros=None, valores=None, oficio=None):
    if erros is None:
        erros = []
    if valores is None:
        valores = {}

    # Monta formulário alunos
    form_alunos = gerar_formulario('alunos', valores, erros, active_tab == 'alunos')
    form_docentes = gerar_formulario('docentes', valores, erros, active_tab == 'docentes')

    conteudo = ''
    if oficio:
        # Página de sucesso
        conteudo = '<h2>Solicitação registrada</h2><pre>' + html_module.escape(oficio) + '</pre>'
    else:
        tabs_html = '''<div class="tabs">
            <div class="tab {cls_alunos}" onclick="showTab(0)">ALUNOS</div>
            <div class="tab {cls_docentes}" onclick="showTab(1)">DOCENTES</div>
        </div>'''.format(
            cls_alunos='active' if active_tab == 'alunos' else '',
            cls_docentes='active' if active_tab == 'docentes' else ''
        )
        forms_html = '''<div class="form {cls_alunos}" id="form-alunos">{form_alunos}</div>
        <div class="form {cls_docentes}" id="form-docentes">{form_docentes}</div>'''.format(
            cls_alunos='active' if active_tab == 'alunos' else '',
            cls_docentes='active' if active_tab == 'docentes' else '',
            form_alunos=form_alunos,
            form_docentes=form_docentes
        )
        conteudo = tabs_html + forms_html

    return BASE_TEMPLATE.replace('{conteudo}', conteudo)

def gerar_formulario(tipo, valores, erros, ativo):
    # valores: dict com chaves de campo
    # erros: lista de strings de erro
    # tipo: 'alunos' ou 'docentes'

    # Input helpers
    def input_text(name, placeholder='', value=''):
        esc_value = html_module.escape(value)
        return '<input type="text" name="{}" placeholder="{}" value="{}">'.format(name, placeholder, esc_value)

    def input_select(name, options, selected=''):
        opts = ''
        for opt in options:
            sel = ' selected' if opt == selected else ''
            opts += '<option value="{}"{}>{}</option>'.format(html_module.escape(opt), sel, html_module.escape(opt))
        return '<select name="{}" required><option value="">Selecione</option>{}</select>'.format(name, opts)

    def input_textarea(name, placeholder='', value=''):
        esc_value = html_module.escape(value)
        return '<textarea name="{}" placeholder="{}" required>{}</textarea>'.format(name, placeholder, esc_value)

    def label(label_text, inner):
        return '<label><span>{}</span>{}</label>'.format(label_text, inner)

    bloco_solicitante = ''
    bloco_solicitante += label('NOME COMPLETO - SEM ABREVIAR', input_text('nome_completo_sem_abreviar', 'Ex.: João da Silva', valores.get('nome_completo_sem_abreviar', '')))
    bloco_solicitante += label('N. USP', input_text('n_usp', 'Apenas números', valores.get('n_usp', '')))
    bloco_solicitante += label('PROGRAMA', input_text('programa', 'Ex.: Ciência da Computação', valores.get('programa', '')))
    if tipo == 'alunos':
        bloco_solicitante += label('NÍVEL', input_select('nivel', ['Mestrado', 'Doutorado'], valores.get('nivel', '')))
        bloco_solicitante += label('TIPO DE AUXÍLIO', input_select('tipo_de_auxilio', ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], valores.get('tipo_de_auxilio', '')))
    bloco_solicitante += label('E-MAIL', input_text('e_mail', 'email@exemplo.com', valores.get('e_mail', '')))
    bloco_solicitante += label('NOME DO EVENTO / BANCA DE EXAME OU DEFESA', input_text('nome_do_evento_banca_de_exame_ou_defesa', 'Ex.: SBRC 2023', valores.get('nome_do_evento_banca_de_exame_ou_defesa', '')))
    bloco_solicitante += label('PERÍODO DO EVENTO, EXAME OU DEFESA', input_text('periodo_do_evento_exame_ou_defesa', 'Ex.: 01/01 a 05/01', valores.get('periodo_do_evento_exame_ou_defesa', '')))
    bloco_solicitante += label('CIDADE DO EVENTO, EXAME OU DEFESA', input_text('cidade_do_evento_exame_ou_defesa', 'Ex.: São Paulo', valores.get('cidade_do_evento_exame_ou_defesa', '')))
    bloco_solicitante += label('ESTADO DO EVENTO, EXAME OU DEFESA', input_text('estado_do_evento_exame_ou_defesa', 'Ex.: SP', valores.get('estado_do_evento_exame_ou_defesa', '')))
    bloco_solicitante += label('PAÍS DO EVENTO, EXAME OU DEFESA', input_text('pais_do_evento_exame_ou_defesa', 'Ex.: Brasil', valores.get('pais_do_evento_exame_ou_defesa', '')))
    bloco_solicitante += label('LINK DO EVENTO, EXAME OU DEFESA', input_text('link_do_evento_exame_ou_defesa', 'Ex.: https://...', valores.get('link_do_evento_exame_ou_defesa', '')))
    bloco_solicitante += label('VALOR SOLICITADO (R$)', input_text('valor_solicitado', 'Ex.: 1500', valores.get('valor_solicitado', '')))
    bloco_solicitante += label('DETALHAMENTO DO PEDIDO', input_textarea('detalhamento_do_pedido', 'Descreva o pedido', valores.get('detalhamento_do_pedido', '')))
    bloco_solicitante += label('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', input_select('ira_apresentar_trabalho_no_evento_que_tipo', ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], valores.get('ira_apresentar_trabalho_no_evento_que_tipo', '')))

    bloco_endereco = ''
    bloco_endereco += label('DATA DE NASCIMENTO', input_text('data_de_nascimento', 'dd/mm/aaaa', valores.get('data_de_nascimento', '')))
    bloco_endereco += label('LOGRADOURO', input_text('logradouro', 'Ex.: Rua', valores.get('logradouro', '')))
    bloco_endereco += label('NÚMERO', input_text('numero', 'Ex.: 100', valores.get('numero', '')))
    bloco_endereco += label('COMPLEMENTO', input_text('complemento', 'Ex.: Apto 10', valores.get('complemento', '')))
    bloco_endereco += label('BAIRRO', input_text('bairro', 'Ex.: Centro', valores.get('bairro', '')))
    bloco_endereco += label('CEP', input_text('cep', '00000-000', valores.get('cep', '')))
    bloco_endereco += label('CIDADE', input_text('cidade', 'Ex.: São Paulo', valores.get('cidade', '')))
    bloco_endereco += label('ESTADO', input_text('estado', 'Ex.: SP', valores.get('estado', '')))

    bloco_pagamento = ''
    bloco_pagamento += label('CPF (SEPARADOS POR PONTOS E TRAÇO)', input_text('cpf', '000.000.000-00', valores.get('cpf', '')))
    bloco_pagamento += label('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', input_text('rg_rnm', '00.000.000-0', valores.get('rg_rnm', '')))
    bloco_pagamento += label('NOME DO BANCO', input_text('nome_do_banco', 'Ex.: Banco do Brasil', valores.get('nome_do_banco', '')))
    bloco_pagamento += label('NÚMERO DA AGÊNCIA', input_text('numero_da_agencia', 'Apenas números', valores.get('numero_da_agencia', '')))
    bloco_pagamento += label('NÚMERO DA CONTA', input_text('numero_da_conta', 'Ex.: 12345-6', valores.get('numero_da_conta', '')))

    erros_html = ''
    if ativo and erros:
        erros_html = '<div class="errors">' + '<br>'.join(erros) + '</div>'

    form = '''<h3>SOLICITANTE E EVENTO</h3>
<div class="bloco">{bloco_solicitante}</div>
<h3>ENDEREÇO DO SOLICITANTE</h3>
<div class="bloco">{bloco_endereco}</div>
<h3>INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</h3>
<div class="bloco">{bloco_pagamento}</div>
{erros}
<button>Enviar solicitação</button>'''.format(
        bloco_solicitante=bloco_solicitante,
        bloco_endereco=bloco_endereco,
        bloco_pagamento=bloco_pagamento,
        erros=erros_html
    )
    return form


# -----------------------------------
# Lógica principal
# -----------------------------------

@app.route('/', methods=['GET', 'POST'])
async def homepage(request: Request):
    if request.method == 'GET':
        html = render_page('alunos')
        return HTMLResponse(html)

    # POST
    data = await request.form()
    active_tab = data.get('active_tab', 'alunos')
    # Se não tem active_tab, inferir pela presença de nivel/tipo
    if 'active_tab' not in data:
        if 'nivel' in data or 'tipo_de_auxilio' in data:
            active_tab = 'alunos'
        else:
            active_tab = 'docentes'
    else:
        active_tab = data['active_tab']

    # Extrai valores
    valores = {}
    campos = [
        'nome_completo_sem_abreviar', 'n_usp', 'programa', 'nivel', 'tipo_de_auxilio',
        'e_mail', 'nome_do_evento_banca_de_exame_ou_defesa', 'periodo_do_evento_exame_ou_defesa',
        'cidade_do_evento_exame_ou_defesa', 'estado_do_evento_exame_ou_defesa', 'pais_do_evento_exame_ou_defesa',
        'link_do_evento_exame_ou_defesa', 'valor_solicitado', 'detalhamento_do_pedido',
        'ira_apresentar_trabalho_no_evento_que_tipo', 'data_de_nascimento', 'logradouro', 'numero',
        'complemento', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_do_banco',
        'numero_da_agencia', 'numero_da_conta'
    ]
    for campo in campos:
        valores[campo] = data.get(campo, '')

    # Validação
    erros = []
    # Campos obrigatórios
    obrigatorios_aluno = [
        'nome_completo_sem_abreviar', 'n_usp', 'programa', 'nivel', 'tipo_de_auxilio',
        'e_mail', 'nome_do_evento_banca_de_exame_ou_defesa', 'periodo_do_evento_exame_ou_defesa',
        'cidade_do_evento_exame_ou_defesa', 'estado_do_evento_exame_ou_defesa', 'pais_do_evento_exame_ou_defesa',
        'valor_solicitado', 'detalhamento_do_pedido', 'ira_apresentar_trabalho_no_evento_que_tipo',
        'data_de_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
        'cpf', 'rg_rnm', 'nome_do_banco', 'numero_da_agencia', 'numero_da_conta'
    ]
    obrigatorios_docente = [
        'nome_completo_sem_abreviar', 'n_usp', 'programa',
        'e_mail', 'nome_do_evento_banca_de_exame_ou_defesa', 'periodo_do_evento_exame_ou_defesa',
        'cidade_do_evento_exame_ou_defesa', 'estado_do_evento_exame_ou_defesa', 'pais_do_evento_exame_ou_defesa',
        'valor_solicitado', 'detalhamento_do_pedido', 'ira_apresentar_trabalho_no_evento_que_tipo',
        'data_de_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
        'cpf', 'rg_rnm', 'nome_do_banco', 'numero_da_agencia', 'numero_da_conta'
    ]
    if active_tab == 'alunos':
        obrigatorios = obrigatorios_aluno
    else:
        obrigatorios = obrigatorios_docente

    required_empty = any(valores[c].strip() == '' for c in obrigatorios)
    if required_empty:
        erros.append('Preencha todos os campos')

    # Validações específicas
    nusp = valores.get('n_usp', '')
    if nusp and not nusp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = valores.get('numero_da_agencia', '')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = valores.get('valor_solicitado', '')
    if valor and not validar_valor(valor):
        erros.append('Valor solicitado deve ser maior que 0')

    email = valores.get('e_mail', '')
    if email and not validar_email(email):
        erros.append('E-mail inválido')

    cpf = valores.get('cpf', '')
    if cpf and not validar_cpf(cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')

    cep = valores.get('cep', '')
    if cep and not validar_cep(cep):
        erros.append('CEP deve estar no formato 00000-000')

    data_nasc = valores.get('data_de_nascimento', '')
    if data_nasc and not validar_data(data_nasc):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    if erros:
        html = render_page(active_tab, erros, valores)
        return HTMLResponse(html)

    # Geração do ofício
    if active_tab == 'alunos':
        oficio_tmpl = OFICIO_ALUNO
        link_line = ''
        if valores['link_do_evento_exame_ou_defesa'].strip():
            link_line = 'Link do evento: ' + valores['link_do_evento_exame_ou_defesa']
        oficio = oficio_tmpl.format(
            nome=valores['nome_completo_sem_abreviar'],
            nusp=valores['n_usp'],
            email=valores['e_mail'],
            tipo=valores['tipo_de_auxilio'],
            programa=valores['programa'],
            nivel=valores['nivel'],
            evento=valores['nome_do_evento_banca_de_exame_ou_defesa'],
            periodo=valores['periodo_do_evento_exame_ou_defesa'],
            cidade_evento=valores['cidade_do_evento_exame_ou_defesa'],
            estado_evento=valores['estado_do_evento_exame_ou_defesa'],
            pais_evento=valores['pais_do_evento_exame_ou_defesa'],
            link=link_line,
            apresentacao=valores['ira_apresentar_trabalho_no_evento_que_tipo'],
            valor=valores['valor_solicitado'],
            detalhamento=valores['detalhamento_do_pedido'],
            endereco=valores['logradouro'] + ', ' + valores['numero'],
            complemento=('Complemento: ' + valores['complemento']) if valores['complemento'].strip() else '',
            cep=valores['cep'],
            bairro=valores['bairro'],
            cidade=valores['cidade'],
            estado=valores['estado'],
            data_nasc=valores['data_de_nascimento'],
            cpf=valores['cpf'],
            rg=valores['rg_rnm'],
            banco=valores['nome_do_banco'],
            agencia=valores['numero_da_agencia'],
            conta=valores['numero_da_conta']
        )
    else:
        oficio_tmpl = OFICIO_DOCENTE
        link_line = ''
        if valores['link_do_evento_exame_ou_defesa'].strip():
            link_line = 'Link do evento: ' + valores['link_do_evento_exame_ou_defesa']
        oficio = oficio_tmpl.format(
            nome=valores['nome_completo_sem_abreviar'],
            nusp=valores['n_usp'],
            email=valores['e_mail'],
            programa=valores['programa'],
            evento=valores['nome_do_evento_banca_de_exame_ou_defesa'],
            periodo=valores['periodo_do_evento_exame_ou_defesa'],
            cidade_evento=valores['cidade_do_evento_exame_ou_defesa'],
            estado_evento=valores['estado_do_evento_exame_ou_defesa'],
            pais_evento=valores['pais_do_evento_exame_ou_defesa'],
            link=link_line,
            apresentacao=valores['ira_apresentar_trabalho_no_evento_que_tipo'],
            valor=valores['valor_solicitado'],
            detalhamento=valores['detalhamento_do_pedido'],
            endereco=valores['logradouro'] + ', ' + valores['numero'],
            complemento=('Complemento: ' + valores['complemento']) if valores['complemento'].strip() else '',
            cep=valores['cep'],
            bairro=valores['bairro'],
            cidade=valores['cidade'],
            estado=valores['estado'],
            data_nasc=valores['data_de_nascimento'],
            cpf=valores['cpf'],
            rg=valores['rg_rnm'],
            banco=valores['nome_do_banco'],
            agencia=valores['numero_da_agencia'],
            conta=valores['numero_da_conta']
        )

    html = render_page(active_tab, oficio=oficio)
    return HTMLResponse(html)
