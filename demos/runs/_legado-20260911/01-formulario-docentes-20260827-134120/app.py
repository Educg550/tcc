from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from typing import Optional
import re

app = FastAPI()

@app.get('/')
async def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())

@app.post('/submit')
async def submit(request: Request, aba: str = Form(...), **data):
    erros = []

    # Validações - Alunos adicional
    if aba == 'ALUNOS':
        campos_obrigatorios = [
            'NOME COMPLETO - SEM ABREVIAR', 'N. USP', 'PROGRAMA', 'NÍVEL', 'TIPO DE AUXÍLIO',
            'E-MAIL', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'PERÍODO DO EVENTO, EXAME OU DEFESA',
            'CIDADE DO EVENTO, EXAME OU DEFESA', 'ESTADO DO EVENTO, EXAME OU DEFESA',
            'PAÍS DO EVENTO, EXAME OU DEFESA', 'VALOR SOLICITADO (R$)', 'DETALHAMENTO DO PEDIDO',
            'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'DATA DE NASCIMENTO', 'LOGRADOURO',
            'NÚMERO', 'BAIRRO', 'CEP', 'CIDADE', 'ESTADO', 'CPF (SEPARADOS POR PONTOS E TRAÇO)',
            'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', 'NOME DO BANCO', 'NÚMERO DA AGÊNCIA', 'NÚMERO DA CONTA'
        ]
    else:
        campos_obrigatorios = [
            'NOME COMPLETO - SEM ABREVIAR', 'N. USP', 'PROGRAMA',
            'E-MAIL', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'PERÍODO DO EVENTO, EXAME OU DEFESA',
            'CIDADE DO EVENTO, EXAME OU DEFESA', 'ESTADO DO EVENTO, EXAME OU DEFESA',
            'PAÍS DO EVENTO, EXAME OU DEFESA', 'VALOR SOLICITADO (R$)', 'DETALHAMENTO DO PEDIDO',
            'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'DATA DE NASCIMENTO', 'LOGRADOURO',
            'NÚMERO', 'BAIRRO', 'CEP', 'CIDADE', 'ESTADO', 'CPF (SEPARADOS POR PONTOS E TRAÇO)',
            'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', 'NOME DO BANCO', 'NÚMERO DA AGÊNCIA', 'NÚMERO DA CONTA'
        ]

    vazios = [c for c in campos_obrigatorios if not data.get(c, '').strip()]
    if vazios:
        erros.append('Preencha todos os campos')

    n_usp = data.get('N. USP', '').strip()
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = data.get('NÚMERO DA AGÊNCIA', '').strip()
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor_raw = data.get('VALOR SOLICITADO (R$)', '').strip()
    if valor_raw and not valor_raw.isdigit():
        erros.append('Valor solicitado deve ser maior que 0')
    elif valor_raw and int(valor_raw) == 0:
        erros.append('Valor solicitado deve ser maior que 0')

    email = data.get('E-MAIL', '').strip()
    if email and ('@' not in email or '.' not in email.split('@')[-1]):
        erros.append('E-mail inválido')

    cpf = data.get('CPF (SEPARADOS POR PONTOS E TRAÇO)', '').strip()
    if cpf and not re.match(r'^\d{11}$', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')

    cep = data.get('CEP', '').strip()
    if cep and not re.match(r'^\d{8}$', cep):
        erros.append('CEP deve estar no formato 00000-000')

    data_nasc = data.get('DATA DE NASCIMENTO', '').strip()
    if data_nasc and not re.match(r'^\d{8}$', data_nasc):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    if erros:
        return HTMLResponse(render_form(aba, data, erros))

    # Gerar ofício
    link = data.get('LINK DO EVENTO, EXAME OU DEFESA', '').strip()
    link_linha = f"Link do evento: {link}" if link else ''
    complemento = data.get('COMPLEMENTO', '').strip()
    compl_linha = f"Complemento: {complemento}" if complemento else ''

    # Formatar valor
    valor_int = int(valor_raw)
    valor_str = f"R$ {valor_int // 100:,}.{valor_int % 100:02d}".replace(',', 'X').replace('.', ',').replace('X', '.')

    if aba == 'ALUNOS':
        oficio = f"""Interessada(o): {data['NOME COMPLETO - SEM ABREVIAR']} - {n_usp}
E-mail: {email}
Assunto: Solicitação de Auxílio Financeiro - {data['TIPO DE AUXÍLIO']}
Programa: {data['PROGRAMA']} - {data['NÍVEL']}

A CCP-{data['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {data['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}
Período: {data['PERÍODO DO EVENTO, EXAME OU DEFESA']}
Local: {data['CIDADE DO EVENTO, EXAME OU DEFESA']} - {data['ESTADO DO EVENTO, EXAME OU DEFESA']} - {data['PAÍS DO EVENTO, EXAME OU DEFESA']}
{link_linha}
Apresentação de trabalho: {data['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}
Valor solicitado: {valor_str}
Detalhamento: {data['DETALHAMENTO DO PEDIDO']}

Endereço da(o) interessada(o)
{data['LOGRADOURO']}, {data['NÚMERO']}
{compl_linha}
CEP: {format_cep(cep)}
{data['BAIRRO']}, {data['CIDADE']} - {data['ESTADO']}

Dados para pagamento
Data de nascimento: {format_data(data_nasc)}
CPF: {format_cpf(cpf)}
RG / RNM: {data['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}
Banco: {data['NOME DO BANCO']}
Agência: {agencia}
Conta: {data['NÚMERO DA CONTA']}

Encaminhe-se ao Serviço Financeiro para providências."""
    else:
        oficio = f"""Interessada(o): {data['NOME COMPLETO - SEM ABREVIAR']} - {n_usp}
E-mail: {email}
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: {data['PROGRAMA']}

A CCP-{data['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {data['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}
Período: {data['PERÍODO DO EVENTO, EXAME OU DEFESA']}
Local: {data['CIDADE DO EVENTO, EXAME OU DEFESA']} - {data['ESTADO DO EVENTO, EXAME OU DEFESA']} - {data['PAÍS DO EVENTO, EXAME OU DEFESA']}
{link_linha}
Apresentação de trabalho: {data['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}
Valor solicitado: {valor_str}
Detalhamento: {data['DETALHAMENTO DO PEDIDO']}

Endereço da(o) interessada(o)
{data['LOGRADOURO']}, {data['NÚMERO']}
{compl_linha}
CEP: {format_cep(cep)}
{data['BAIRRO']}, {data['CIDADE']} - {data['ESTADO']}

Dados para pagamento
Data de nascimento: {format_data(data_nasc)}
CPF: {format_cpf(cpf)}
RG / RNM: {data['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}
Banco: {data['NOME DO BANCO']}
Agência: {agencia}
Conta: {data['NÚMERO DA CONTA']}

Encaminhe-se ao Serviço Financeiro para providências."""

    oficio_lines = [l for l in oficio.split('\n') if l.strip() != '' and not l.startswith('Link do evento: ') and not l.startswith('Complemento: ')]
    oficio = '\n'.join(oficio_lines)
    # Reconstruir com link e complemento se não vazios
    oficio = f"""Interessada(o): {data['NOME COMPLETO - SEM ABREVIAR']} - {n_usp}
E-mail: {email}
Assunto: Solicitação de Auxílio Financeiro - { 'Verba do programa' if aba == 'DOCENTES' else data['TIPO DE AUXÍLIO'] }
Programa: {data['PROGRAMA']}{ ('' if aba == 'DOCENTES' else ' - ' + data['NÍVEL']) }

A CCP-{data['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {data['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}
Período: {data['PERÍODO DO EVENTO, EXAME OU DEFESA']}
Local: {data['CIDADE DO EVENTO, EXAME OU DEFESA']} - {data['ESTADO DO EVENTO, EXAME OU DEFESA']} - {data['PAÍS DO EVENTO, EXAME OU DEFESA']}
{link_linha + chr(10) if link_linha else ''}Apresentação de trabalho: {data['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}
Valor solicitado: {valor_str}
Detalhamento: {data['DETALHAMENTO DO PEDIDO']}

Endereço da(o) interessada(o)
{data['LOGRADOURO']}, {data['NÚMERO']}
{compl_linha + chr(10) if compl_linha else ''}CEP: {format_cep(cep)}
{data['BAIRRO']}, {data['CIDADE']} - {data['ESTADO']}

Dados para pagamento
Data de nascimento: {format_data(data_nasc)}
CPF: {format_cpf(cpf)}
RG / RNM: {data['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}
Banco: {data['NOME DO BANCO']}
Agência: {agencia}
Conta: {data['NÚMERO DA CONTA']}

Encaminhe-se ao Serviço Financeiro para providências."""
    # Remover linhas vazias extras
    oficio = '\n'.join([l for l in oficio.split('\n') if l.strip()])

    return HTMLResponse(render_confirmacao(aba, oficio, data))


def format_cep(s):
    if len(s) == 8:
        return f'{s[:5]}-{s[5:]}'
    return s

def format_cpf(s):
    if len(s) == 11:
        return f'{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}'
    return s

def format_data(s):
    if len(s) == 8:
        return f'{s[:2]}/{s[2:4]}/{s[4:]}'
    return s

def render_form(aba, data, erros):
    # Implementação inline no HTML
    # Recriar o HTML com dados preservados
    msg_erro = ''
    if erros:
        msg_erro = '<div class="erros">' + '<br>'.join(erros) + '</div>'
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
.container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
.cabecalho {{ text-align: center; margin-bottom: 20px; color: #003366; }}
.cabecalho img {{ max-width: 200px; }}
.abas {{ display: flex; margin-bottom: 10px; }}
.aba {{ padding: 10px 20px; cursor: pointer; border: 1px solid #ccc; background: #f0f0f0; }}
.aba.ativa {{ background: #003366; color: white; font-weight: bold; }}
.formulario {{ display: none; }}
.formulario.ativo {{ display: block; }}
.bloco {{ border: 1px solid #ccc; padding: 15px; margin-top: 20px; }}
.bloco h2 {{ margin-top: 0; color: #003366; }}
.campo {{ margin-bottom: 15px; }}
.campo label {{ display: block; font-weight: bold; margin-bottom: 3px; }}
.campo input, .campo select, .campo textarea {{ width: 100%; padding: 8px; box-sizing: border-box; }}
.erros {{ color: red; margin-bottom: 15px; }}
button {{ background-color: #003366; color: white; padding: 10px 20px; border: none; cursor: pointer; font-size: 16px; }}
</style>
</head>
<body>
<div class="container">
<div class="cabecalho">
<img src="/images/usp-logo.png" alt="USP">
<h1>Universidade de São Paulo</h1>
<h2>Instituto de Matemática e Estatística</h2>
<h3>Pós-Graduação</h3>
</div>
<div class="abas">
<div class="aba {'ativa' if aba == 'ALUNOS' else ''}" onclick="mostrarAba('ALUNOS')">ALUNOS</div>
<div class="aba {'ativa' if aba == 'DOCENTES' else ''}" onclick="mostrarAba('DOCENTES')">DOCENTES</div>
</div>
{msg_erro}
<form id="form-ALUNOS" class="formulario {'ativo' if aba == 'ALUNOS' else ''}" method="post" action="/submit">
<input type="hidden" name="aba" value="ALUNOS">
<div class="bloco">
<h2>SOLICITANTE E EVENTO</h2>
<div class="campo"><label>NOME COMPLETO - SEM ABREVIAR</label><input type="text" name="NOME COMPLETO - SEM ABREVIAR" placeholder="João Silva" value="{escape(data.get('NOME COMPLETO - SEM ABREVIAR',''))}" required></div>
<div class="campo"><label>N. USP</label><input type="text" name="N. USP" placeholder="12345678" value="{escape(data.get('N. USP',''))}" required></div>
<div class="campo"><label>PROGRAMA</label><input type="text" name="PROGRAMA" placeholder="Matemática" value="{escape(data.get('PROGRAMA',''))}" required></div>
<div class="campo"><label>NÍVEL</label><select name="NÍVEL" required><option value="Mestrado" {'selected' if data.get('NÍVEL') == 'Mestrado' else ''}>Mestrado</option><option value="Doutorado" {'selected' if data.get('NÍVEL') == 'Doutorado' else ''}>Doutorado</option></select></div>
<div class="campo"><label>TIPO DE AUXÍLIO</label><select name="TIPO DE AUXÍLIO" required><option value="Participação em evento" {'selected' if data.get('TIPO DE AUXÍLIO') == 'Participação em evento' else ''}>Participação em evento</option><option value="Banca de exame ou defesa" {'selected' if data.get('TIPO DE AUXÍLIO') == 'Banca de exame ou defesa' else ''}>Banca de exame ou defesa</option><option value="Outro" {'selected' if data.get('TIPO DE AUXÍLIO') == 'Outro' else ''}>Outro</option></select></div>
<div class="campo"><label>E-MAIL</label><input type="text" name="E-MAIL" placeholder="exemplo@usp.br" value="{escape(data.get('E-MAIL',''))}" required></div>
<div class="campo"><label>NOME DO EVENTO / BANCA DE EXAME OU DEFESA</label><input type="text" name="NOME DO EVENTO / BANCA DE EXAME OU DEFESA" placeholder="Ex.: Congresso de Matemática" value="{escape(data.get('NOME DO EVENTO / BANCA DE EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>PERÍODO DO EVENTO, EXAME OU DEFESA</label><input type="text" name="PERÍODO DO EVENTO, EXAME OU DEFESA" placeholder="01/03/2025 a 05/03/2025" value="{escape(data.get('PERÍODO DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>CIDADE DO EVENTO, EXAME OU DEFESA</label><input type="text" name="CIDADE DO EVENTO, EXAME OU DEFESA" placeholder="São Paulo" value="{escape(data.get('CIDADE DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>ESTADO DO EVENTO, EXAME OU DEFESA</label><input type="text" name="ESTADO DO EVENTO, EXAME OU DEFESA" placeholder="SP" value="{escape(data.get('ESTADO DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>PAÍS DO EVENTO, EXAME OU DEFESA</label><input type="text" name="PAÍS DO EVENTO, EXAME OU DEFESA" placeholder="Brasil" value="{escape(data.get('PAÍS DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>LINK DO EVENTO, EXAME OU DEFESA (opcional)</label><input type="text" name="LINK DO EVENTO, EXAME OU DEFESA" placeholder="https://exemplo.com" value="{escape(data.get('LINK DO EVENTO, EXAME OU DEFESA',''))}"></div>
<div class="campo"><label>VALOR SOLICITADO (R$)</label><input type="text" name="VALOR SOLICITADO (R$)" placeholder="1500" value="{escape(data.get('VALOR SOLICITADO (R$)',''))}" required></div>
<div class="campo"><label>DETALHAMENTO DO PEDIDO</label><textarea name="DETALHAMENTO DO PEDIDO" placeholder="Descreva o pedido" required>{escape(data.get('DETALHAMENTO DO PEDIDO',''))}</textarea></div>
<div class="campo"><label>IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?</label><select name="IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?" required><option value="Pôster" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Pôster' else ''}>Pôster</option><option value="Apresentação oral" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Apresentação oral' else ''}>Apresentação oral</option><option value="Outra" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Outra' else ''}>Outra</option><option value="Não irá apresentar trabalho" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Não irá apresentar trabalho' else ''}>Não irá apresentar trabalho</option></select></div>
</div>
<div class="bloco">
<h2>ENDEREÇO DO SOLICITANTE</h2>
<div class="campo"><label>DATA DE NASCIMENTO</label><input type="text" name="DATA DE NASCIMENTO" placeholder="01021990" value="{escape(data.get('DATA DE NASCIMENTO',''))}" required></div>
<div class="campo"><label>LOGRADOURO</label><input type="text" name="LOGRADOURO" placeholder="Rua A" value="{escape(data.get('LOGRADOURO',''))}" required></div>
<div class="campo"><label>NÚMERO</label><input type="text" name="NÚMERO" placeholder="100" value="{escape(data.get('NÚMERO',''))}" required></div>
<div class="campo"><label>COMPLEMENTO (opcional)</label><input type="text" name="COMPLEMENTO" placeholder="Apto 5" value="{escape(data.get('COMPLEMENTO',''))}"></div>
<div class="campo"><label>BAIRRO</label><input type="text" name="BAIRRO" placeholder="Centro" value="{escape(data.get('BAIRRO',''))}" required></div>
<div class="campo"><label>CEP</label><input type="text" name="CEP" placeholder="05508090" value="{escape(data.get('CEP',''))}" required></div>
<div class="campo"><label>CIDADE</label><input type="text" name="CIDADE" placeholder="São Paulo" value="{escape(data.get('CIDADE',''))}" required></div>
<div class="campo"><label>ESTADO</label><input type="text" name="ESTADO" placeholder="SP" value="{escape(data.get('ESTADO',''))}" required></div>
</div>
<div class="bloco">
<h2>INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</h2>
<div class="campo"><label>CPF (SEPARADOS POR PONTOS E TRAÇO)</label><input type="text" name="CPF (SEPARADOS POR PONTOS E TRAÇO)" placeholder="12345678901" value="{escape(data.get('CPF (SEPARADOS POR PONTOS E TRAÇO)',''))}" required></div>
<div class="campo"><label>RG / RNM (SEPARADOS POR PONTOS E TRAÇO)</label><input type="text" name="RG / RNM (SEPARADOS POR PONTOS E TRAÇO)" placeholder="12.345.678-9" value="{escape(data.get('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',''))}" required></div>
<div class="campo"><label>NOME DO BANCO</label><input type="text" name="NOME DO BANCO" placeholder="Banco do Brasil" value="{escape(data.get('NOME DO BANCO',''))}" required></div>
<div class="campo"><label>NÚMERO DA AGÊNCIA</label><input type="text" name="NÚMERO DA AGÊNCIA" placeholder="1234" value="{escape(data.get('NÚMERO DA AGÊNCIA',''))}" required></div>
<div class="campo"><label>NÚMERO DA CONTA</label><input type="text" name="NÚMERO DA CONTA" placeholder="56789-0" value="{escape(data.get('NÚMERO DA CONTA',''))}" required></div>
</div>
<button type="submit">Enviar solicitação</button>
</form>
<form id="form-DOCENTES" class="formulario {'ativo' if aba == 'DOCENTES' else ''}" method="post" action="/submit">
<input type="hidden" name="aba" value="DOCENTES">
<div class="bloco">
<h2>SOLICITANTE E EVENTO</h2>
<div class="campo"><label>NOME COMPLETO - SEM ABREVIAR</label><input type="text" name="NOME COMPLETO - SEM ABREVIAR" placeholder="João Silva" value="{escape(data.get('NOME COMPLETO - SEM ABREVIAR',''))}" required></div>
<div class="campo"><label>N. USP</label><input type="text" name="N. USP" placeholder="12345678" value="{escape(data.get('N. USP',''))}" required></div>
<div class="campo"><label>PROGRAMA</label><input type="text" name="PROGRAMA" placeholder="Matemática" value="{escape(data.get('PROGRAMA',''))}" required></div>
<div class="campo"><label>E-MAIL</label><input type="text" name="E-MAIL" placeholder="exemplo@usp.br" value="{escape(data.get('E-MAIL',''))}" required></div>
<div class="campo"><label>NOME DO EVENTO / BANCA DE EXAME OU DEFESA</label><input type="text" name="NOME DO EVENTO / BANCA DE EXAME OU DEFESA" placeholder="Ex.: Congresso de Matemática" value="{escape(data.get('NOME DO EVENTO / BANCA DE EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>PERÍODO DO EVENTO, EXAME OU DEFESA</label><input type="text" name="PERÍODO DO EVENTO, EXAME OU DEFESA" placeholder="01/03/2025 a 05/03/2025" value="{escape(data.get('PERÍODO DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>CIDADE DO EVENTO, EXAME OU DEFESA</label><input type="text" name="CIDADE DO EVENTO, EXAME OU DEFESA" placeholder="São Paulo" value="{escape(data.get('CIDADE DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>ESTADO DO EVENTO, EXAME OU DEFESA</label><input type="text" name="ESTADO DO EVENTO, EXAME OU DEFESA" placeholder="SP" value="{escape(data.get('ESTADO DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>PAÍS DO EVENTO, EXAME OU DEFESA</label><input type="text" name="PAÍS DO EVENTO, EXAME OU DEFESA" placeholder="Brasil" value="{escape(data.get('PAÍS DO EVENTO, EXAME OU DEFESA',''))}" required></div>
<div class="campo"><label>LINK DO EVENTO, EXAME OU DEFESA (opcional)</label><input type="text" name="LINK DO EVENTO, EXAME OU DEFESA" placeholder="https://exemplo.com" value="{escape(data.get('LINK DO EVENTO, EXAME OU DEFESA',''))}"></div>
<div class="campo"><label>VALOR SOLICITADO (R$)</label><input type="text" name="VALOR SOLICITADO (R$)" placeholder="1500" value="{escape(data.get('VALOR SOLICITADO (R$)',''))}" required></div>
<div class="campo"><label>DETALHAMENTO DO PEDIDO</label><textarea name="DETALHAMENTO DO PEDIDO" placeholder="Descreva o pedido" required>{escape(data.get('DETALHAMENTO DO PEDIDO',''))}</textarea></div>
<div class="campo"><label>IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?</label><select name="IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?" required><option value="Pôster" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Pôster' else ''}>Pôster</option><option value="Apresentação oral" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Apresentação oral' else ''}>Apresentação oral</option><option value="Outra" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Outra' else ''}>Outra</option><option value="Não irá apresentar trabalho" {'selected' if data.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?') == 'Não irá apresentar trabalho' else ''}>Não irá apresentar trabalho</option></select></div>
</div>
<div class="bloco">
<h2>ENDEREÇO DO SOLICITANTE</h2>
<div class="campo"><label>DATA DE NASCIMENTO</label><input type="text" name="DATA DE NASCIMENTO" placeholder="01021990" value="{escape(data.get('DATA DE NASCIMENTO',''))}" required></div>
<div class="campo"><label>LOGRADOURO</label><input type="text" name="LOGRADOURO" placeholder="Rua A" value="{escape(data.get('LOGRADOURO',''))}" required></div>
<div class="campo"><label>NÚMERO</label><input type="text" name="NÚMERO" placeholder="100" value="{escape(data.get('NÚMERO',''))}" required></div>
<div class="campo"><label>COMPLEMENTO (opcional)</label><input type="text" name="COMPLEMENTO" placeholder="Apto 5" value="{escape(data.get('COMPLEMENTO',''))}"></div>
<div class="campo"><label>BAIRRO</label><input type="text" name="BAIRRO" placeholder="Centro" value="{escape(data.get('BAIRRO',''))}" required></div>
<div class="campo"><label>CEP</label><input type="text" name="CEP" placeholder="05508090" value="{escape(data.get('CEP',''))}" required></div>
<div class="campo"><label>CIDADE</label><input type="text" name="CIDADE" placeholder="São Paulo" value="{escape(data.get('CIDADE',''))}" required></div>
<div class="campo"><label>ESTADO</label><input type="text" name="ESTADO" placeholder="SP" value="{escape(data.get('ESTADO',''))}" required></div>
</div>
<div class="bloco">
<h2>INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO</h2>
<div class="campo"><label>CPF (SEPARADOS POR PONTOS E TRAÇO)</label><input type="text" name="CPF (SEPARADOS POR PONTOS E TRAÇO)" placeholder="12345678901" value="{escape(data.get('CPF (SEPARADOS POR PONTOS E TRAÇO)',''))}" required></div>
<div class="campo"><label>RG / RNM (SEPARADOS POR PONTOS E TRAÇO)</label><input type="text" name="RG / RNM (SEPARADOS POR PONTOS E TRAÇO)" placeholder="12.345.678-9" value="{escape(data.get('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',''))}" required></div>
<div class="campo"><label>NOME DO BANCO</label><input type="text" name="NOME DO BANCO" placeholder="Banco do Brasil" value="{escape(data.get('NOME DO BANCO',''))}" required></div>
<div class="campo"><label>NÚMERO DA AGÊNCIA</label><input type="text" name="NÚMERO DA AGÊNCIA" placeholder="1234" value="{escape(data.get('NÚMERO DA AGÊNCIA',''))}" required></div>
<div class="campo"><label>NÚMERO DA CONTA</label><input type="text" name="NÚMERO DA CONTA" placeholder="56789-0" value="{escape(data.get('NÚMERO DA CONTA',''))}" required></div>
</div>
<button type="submit">Enviar solicitação</button>
</form>
</div>
<script>
function mostrarAba(aba) {{
    document.querySelectorAll('.formulario').forEach(f => f.classList.remove('ativo'));
    document.querySelectorAll('.aba').forEach(a => a.classList.remove('ativa'));
    document.getElementById('form-' + aba).classList.add('ativo');
    document.querySelector('.aba[onclick*="' + aba + '"]').classList.add('ativa');
}}
</script>
</body>
</html>"""

def render_confirmacao(aba, oficio, data):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Solicitação registrada</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
.container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
.cabecalho {{ text-align: center; margin-bottom: 20px; color: #003366; }}
pre {{ white-space: pre-wrap; font-family: inherit; }}
</style>
</head>
<body>
<div class="container">
<div class="cabecalho">
<img src="/images/usp-logo.png" alt="USP">
<h1>Universidade de São Paulo</h1>
<h2>Instituto de Matemática e Estatística</h2>
<h3>Pós-Graduação</h3>
</div>
<h2>Solicitação registrada</h2>
<pre>{escape(oficio)}</pre>
</div>
</body>
</html>"""

def escape(s):
    if s is None:
        return ''
    s = str(s)
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&#39;')
    return s
