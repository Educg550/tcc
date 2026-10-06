from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent

def remove_accents(s: str) -> str:
    if s is None:
        return ""
    # Use unicodedata to normalize and strip accents
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

app = FastAPI()

# Mount static files
app.mount("/", StaticFiles(directory=str(ROOT), html=True), name="static")

@app.post("/solicitacao")
async def solicitacao_post(request: Request):
    data = await request.json()
    aba = data.get("aba", "")
    
    # Normalize inputs
    nome = data.get("nome", "")
    nusp = data.get("nusp", "")
    programa = data.get("programa", "")
    nivel = data.get("nivel", "")
    tipo_auxilio = data.get("tipo_auxilio", "")
    email = data.get("email", "")
    evento = data.get("evento", "")
    periodo = data.get("periodo", "")
    cidade = data.get("cidade", "")
    estado = data.get("estado", "")
    pais = data.get("pais", "")
    link = data.get("link", "")
    valor = data.get("valor", "")
    detalhamento = data.get("detalhamento", "")
    apresentacao = data.get("apresentacao", "")
    data_nascimento = data.get("data_nascimento", "")
    logradouro = data.get("logradouro", "")
    numero = data.get("numero", "")
    complemento = data.get("complemento", "")
    bairro = data.get("bairro", "")
    cep = data.get("cep", "")
    cidade_endereco = data.get("cidade_endereco", "")
    estado_endereco = data.get("estado_endereco", "")
    cpf = data.get("cpf", "")
    rg = data.get("rg", "")
    banco = data.get("banco", "")
    agencia = data.get("agencia", "")
    conta = data.get("conta", "")

    errors = []

    # Check for empty required fields
    required_fields = {
        "nome": nome, "nusp": nusp, "programa": programa, "email": email,
        "evento": evento, "periodo": periodo, "cidade": cidade,
        "estado": estado, "pais": pais, "valor": valor,
        "detalhamento": detalhamento, "apresentacao": apresentacao,
        "data_nascimento": data_nascimento, "logradouro": logradouro,
        "numero": numero, "bairro": bairro, "cep": cep,
        "cidade_endereco": cidade_endereco, "estado_endereco": estado_endereco,
        "cpf": cpf, "rg": rg, "banco": banco, "agencia": agencia, "conta": conta
    }

    if aba == "alunos":
        required_fields["nivel"] = nivel
        required_fields["tipo_auxilio"] = tipo_auxilio

    missing = False
    for k, v in required_fields.items():
        if not v or v.strip() == "":
            missing = True
            break
    
    if missing:
        errors.append("Preencha todos os campos")

    # Format Validation
    
    # N. USP
    if nusp and not nusp.isdigit():
        errors.append("N. USP deve conter apenas numeros")

    # Agencia
    if agencia and not agencia.isdigit():
        errors.append("Numero da agencia deve conter apenas numeros")

    # Valor
    # In tests: valor="150000" -> R$ 1.500,00 (cents)
    # Validation: must be > 0
    if valor:
        # Extract digits from valor if it was formatted with R$ or similar, or just digits
        digits = re.sub(r"\D", "", valor)
        if not digits or int(digits) <= 0:
            errors.append("Valor solicitado deve ser maior que 0")

    # Email
    if email and ("@" not in email or email.endswith("@") or ".." in email):
        errors.append("E-mail invalido")

    # CPF
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            errors.append("CPF deve estar no formato 000.000.000-00")
        else:
            # Check CPF digits
            digits_cpf = re.sub(r"\D", "", cpf)
            if digits_cpf:
                base = digits_cpf[:9]
                d1, d2 = digits_cpf[9:11]
                
                def get_digit(cpf_digits, pos):
                    mult = pos + 1
                    soma = 0
                    for x in range(pos):
                        soma += int(cpf_digits[x]) * mult
                        mult -= 1
                    resto = (soma * 10) % 11
                    return 0 if resto == 10 else resto
                
                calc_d1 = get_digit(base, 9)
                base2 = base + str(calc_d1)
                calc_d2 = get_digit(base2, 10)
                
                if int(d1) != calc_d1 or int(d2) != calc_d2:
                    errors.append("CPF invalido")

    # CEP
    if cep:
        if not re.match(r"^\d{5}-\d{3}$", cep):
            errors.append("CEP deve estar no formato 00000-000")

    # Data de Nascimento
    if data_nascimento:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", data_nascimento):
            errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                day, month, year = map(int, data_nascimento.split("/"))
                if month < 1 or month > 12:
                    raise ValueError
                
                days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    days_in_month[1] = 29
                    
                if day < 1 or day > days_in_month[month - 1]:
                    raise ValueError
            except ValueError:
                errors.append("Data de nascimento invalida")

    if errors:
        return JSONResponse({"erros": errors}, status_code=200)

    # Generate Oficio
    # Format Valor for Oficio
    formatted_valor = ""
    if valor:
        digits = re.sub(r"\D", "", valor)
        cents = int(digits)
        formatted_valor = f"R$ {cents/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        formatted_valor = formatted_valor.replace(". ", ".")

    # Build lines
    lines = []
    lines.append(f"Interessada(o): {nome} - {nusp}")
    lines.append(f"E-mail: {email}")
    
    if aba == "alunos":
        lines.append(f"Assunto: Solicitacao de Auxilio Financeiro - {tipo_auxilio}")
        lines.append(f"Programa: {programa} - {nivel}")
    else:
        lines.append(f"Assunto: Solicitacao de Auxilio Financeiro - Verba do programa")
        lines.append(f"Programa: {programa}")

    lines.append("")
    lines.append("A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append(f"Evento: {evento}")
    lines.append(f"Periodo: {periodo}")
    lines.append(f"Local: {cidade} - {estado} - {pais}")
    
    if link and link.strip():
        lines.append(f"Link do evento: {link}")
        
    lines.append(f"Apresentacao de trabalho: {apresentacao}")
    lines.append(f"Valor solicitado: {formatted_valor}")
    lines.append(f"Detalhamento: {detalhamento}")
    
    lines.append("")
    lines.append("Endereco da(o) interessada(o)")
    lines.append(f"{logradouro}, {numero}")
    
    if complemento and complemento.strip():
        lines.append(f"Complemento: {complemento}")
        
    lines.append(f"CEP: {cep}")
    lines.append(f"{bairro}, {cidade_endereco} - {estado_endereco}")
    
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append(f"Data de nascimento: {data_nascimento}")
    lines.append(f"CPF: {cpf}")
    lines.append(f"RG / RNM: {rg}")
    lines.append(f"Banco: {banco}")
    lines.append(f"Agencia: {agencia}")
    lines.append(f"Conta: {conta}")
    
    lines.append("")
    lines.append("Encaminhe-se ao Servico Financeiro para providencias.")
    
    oficio = "\n".join(lines)
    
    return JSONResponse({"oficio": oficio}, status_code=200)