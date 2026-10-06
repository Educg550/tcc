import re
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

class Solicitacao(BaseModel):
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str = ""
    nome_evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""

def valida_cpf(cpf: str) -> bool:
    digitos = re.sub(r'\D', '', cpf)
    if len(digitos) != 11:
        return False
    if digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[j]) * (i + 1 - j) for j in range(i))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if int(digitos[i]) != esperado:
            return False
    return True

def valida_data(data: str) -> bool:
    m = re.fullmatch(r'(\d{2})/(\d{2})/(\d{4})', data)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mes < 1 or mes > 12 or dia < 1:
        return False
    if mes in (4, 6, 9, 11) and dia > 30:
        return False
    if mes == 2:
        bissexto = (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0)
        if dia > (29 if bissexto else 28):
            return False
    return True

def valor_natural(valor: str) -> bool:
    digitos = re.sub(r'\D', '', valor)
    if not digitos:
        return False
    try:
        return int(digitos) > 0
    except ValueError:
        return False

def formata_moeda(valor: str) -> str:
    digitos = re.sub(r'\D', '', valor)
    if not digitos:
        return 'R$ 0,00'
    inteiro = int(digitos)
    centavos = inteiro % 100
    reais = inteiro // 100
    reais_str = f'{reais:,}'.replace(',', '.')
    return f'R$ {reais_str},{centavos:02d}'

@app.post("/solicitar")
async def solicitar(s: Solicitacao):
    erros = []

    campos_obrigatorios = ['nome', 'n_usp', 'programa', 'email', 'nome_evento',
                           'periodo', 'cidade_evento', 'estado_evento', 'pais_evento',
                           'valor', 'detalhamento', 'apresentacao', 'data_nascimento',
                           'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
                           'cpf', 'rg', 'banco', 'agencia', 'conta']
    if s.tipo_auxilio is not None:
        campos_obrigatorios.append('tipo_auxilio')
    if s.nivel is not None:
        campos_obrigatorios.append('nivel')

    for campo in campos_obrigatorios:
        valor = getattr(s, campo, None)
        if not valor or (isinstance(valor, str) and not valor.strip()):
            erros.append('Preencha todos os campos')
            break

    if s.n_usp and not re.fullmatch(r'\d+', s.n_usp.strip()):
        erros.append('N. USP deve conter apenas números')

    if s.agencia and not re.fullmatch(r'\d+', s.agencia.strip()):
        erros.append('Número da agência deve conter apenas números')

    if s.valor and not valor_natural(s.valor):
        erros.append('Valor solicitado deve ser maior que 0')

    if s.email:
        if '@' not in s.email or '.' not in s.email.split('@')[-1] or not s.email.split('@')[-1]:
            erros.append('E-mail inválido')

    if s.cpf and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', s.cpf.strip()):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif s.cpf and not valida_cpf(s.cpf):
        erros.append('CPF inválido')

    if s.cep and not re.fullmatch(r'\d{5}-\d{3}', s.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')

    if s.data_nascimento and not re.fullmatch(r'\d{2}/\d{2}/\d{4}', s.data_nascimento.strip()):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif s.data_nascimento and not valida_data(s.data_nascimento.strip()):
        erros.append('Data de nascimento inválida')

    if erros:
        return JSONResponse({'erros': erros})

    assunto = f"Solicitação de Auxílio Financeiro - {s.tipo_auxilio}" if s.tipo_auxilio else "Solicitação de Auxílio Financeiro - Verba do programa"
    programa_linha = f"{s.programa} - {s.nivel}" if s.nivel else f"{s.programa}"
    link_linha = f"Link do evento: {s.link_evento}" if s.link_evento and s.link_evento.strip() else ""
    complemento_linha = f"Complemento: {s.complemento}" if s.complemento and s.complemento.strip() else ""
    valor_fmt = formata_moeda(s.valor)

    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        f"Assunto: {assunto}",
        f"Programa: {programa_linha}",
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
        link_linha,
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
        complemento_linha,
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    linhas = [l for l in linhas if l is not None and l != ""]
    oficio = "\n".join(linhas)

    return {"oficio": oficio}