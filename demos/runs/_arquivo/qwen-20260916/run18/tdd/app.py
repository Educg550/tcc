from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

@app.post("/solicitacao")
async def solicitacao(req: Request):
    body = await req.json()
    aba = body.get("aba")
    dados = body.get("dados", {})

    campos_obrigatorios = [
        "nome", "nusp", "programa", "email", "nome_evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta"
    ]
    
    if aba == "alunos":
        campos_obrigatorios.extend(["nivel", "tipo_auxilio"])
        
    erros = []
    
    # Validação de campos vazios (exceto os opcionais link_evento e complemento)
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            erros.append("Preencha todos os campos")
            break # Adiciona a mensagem apenas uma vez
            
    # Validações específicas
    if dados.get("nusp") and not dados["nusp"].isdigit():
        erros.append("N. USP deve conter apenas números")
        
    if dados.get("agencia") and not dados["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
        
    # Validação de valor
    valor_str = dados.get("valor", "").replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        valor_num = float(valor_str)
        if valor_num <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    except ValueError:
        erros.append("Valor solicitado deve ser maior que 0")
        
    # Validação de e-mail
    email = dados.get("email", "")
    if email:
        if "@" not in email or "." not in email.split("@")[-1]:
            erros.append("E-mail inválido")
            
    # Validação de CPF
    cpf = dados.get("cpf", "")
    if cpf:
        cpf_digits = "".join(c for c in cpf if c.isdigit())
        if len(cpf_digits) != 11 or not ("." in cpf and "-" in cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        else:
            # Validação dos dígitos verificadores
            if cpf_digits != "11111111111" and cpf_digits != "22222222222" and cpf_digits != "33333333333" and cpf_digits != "44444444444" and cpf_digits != "55555555555" and cpf_digits != "66666666666" and cpf_digits != "77777777777" and cpf_digits != "88888888888" and cpf_digits != "99999999999" and cpf_digits != "00000000000":
                # Calcula primeiro dígito verificador
                soma = 0
                for i in range(9):
                    soma += int(cpf_digits[i]) * (10 - i)
                dv1 = (soma * 10) % 11
                if dv1 == 10:
                    dv1 = 0
                
                if dv1 != int(cpf_digits[9]):
                    erros.append("CPF inválido")
                else:
                    # Calcula segundo dígito verificador
                    soma = 0
                    for i in range(10):
                        soma += int(cpf_digits[i]) * (11 - i)
                    dv2 = (soma * 10) % 11
                    if dv2 == 10:
                        dv2 = 0
                        
                    if dv2 != int(cpf_digits[10]):
                        erros.append("CPF inválido")
            else:
                erros.append("CPF inválido")

    # Validação de CEP
    cep = dados.get("cep", "")
    if cep:
        cep_digits = "".join(c for c in cep if c.isdigit())
        if len(cep_digits) != 8 or "-" not in cep:
            erros.append("CEP deve estar no formato 00000-000")
            
    # Validação de Data de Nascimento
    data = dados.get("data_nascimento", "")
    if data:
        data_parts = data.split("/")
        if len(data_parts) != 3 or len(data_parts[0]) != 2 or len(data_parts[1]) != 2 or len(data_parts[2]) != 4:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                dia, mes, ano = int(data_parts[0]), int(data_parts[1]), int(data_parts[2])
                if mes < 1 or mes > 12:
                    erros.append("Data de nascimento inválida")
                else:
                    dias_no_mes = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    if dia < 1 or dia > dias_no_mes[mes - 1]:
                        erros.append("Data de nascimento inválida")
            except ValueError:
                erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if erros:
        return JSONResponse(content={"erros": erros}, status_code=200)

    # Geração do Ofício
    tipo_auxilio = dados.get("tipo_auxilio", "Verba do programa")
    nivel = dados.get("nivel", "")
    programa = dados.get("programa", "")
    
    if aba == "docentes":
        assunto_linha = f"Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = f"Programa: {programa}"
    else:
        assunto_linha = f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}"
        programa_linha = f"Programa: {programa} - {nivel}"
        
    link_linha = f"\nLink do evento: {dados['link_evento']}" if dados.get("link_evento") else ""
    compl_linha = f"\nComplemento: {dados['complemento']}" if dados.get("complemento") else ""
    
    oficio = f"""Interessada(o): {dados['nome']} - {dados['nusp']}
E-mail: {dados['email']}
{assunto_linha}
{programa_linha}

A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {dados['nome_evento']}
Período: {dados['periodo']}
Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}{link_linha}
Apresentação de trabalho: {dados['apresentacao']}
Valor solicitado: {dados['valor']}
Detalhamento: {dados['detalhamento']}

Endereço da(o) interessada(o)
{dados['logradouro']}, {dados['numero']}{compl_linha}
CEP: {dados['cep']}
{dados['bairro']}, {dados['cidade']} - {dados['estado']}

Dados para pagamento
Data de nascimento: {dados['data_nascimento']}
CPF: {dados['cpf']}
RG / RNM: {dados['rg']}
Banco: {dados['banco']}
Agência: {dados['agencia']}
Conta: {dados['conta']}

Encaminhe-se ao Serviço Financeiro para providências."""

    return JSONResponse(content={"oficio": oficio}, status_code=200)

app.mount("/", StaticFiles(directory=".", html=True), name="static")
