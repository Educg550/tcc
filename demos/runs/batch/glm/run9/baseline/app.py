import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    estado: str


class Pagamento(BaseModel):
    data_nascimento: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


class Solicitacao(BaseModel):
    aba: str
    nome: str
    n_usp: str
    programa: str
    nivel: str
    tipo_auxilio: str
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
    endereco: Endereco
    pagamento: Pagamento


@staticmethod
def validar_cpf_digitos(cpf: str) -> bool:
    numeros = [int(d) for d in cpf if d.isdigit()]
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False
    soma = sum(numeros[i] * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != numeros[9]:
        return False
    soma = sum(numeros[i] * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    return resto == numeros[10]


def validar(s: Solicitacao) -> list[str]:
    erros = []
    obrigatorios = []
    if s.aba == "alunos":
        obrigatorios = [s.nome, s.n_usp, s.programa, s.nivel, s.tipo_auxilio, s.email,
                        s.evento, s.periodo, s.cidade_evento, s.estado_evento,
                        s.pais_evento, s.valor_solicitado, s.detalhamento, s.apresentacao]
    else:
        obrigatorios = [s.nome, s.n_usp, s.programa, s.email,
                        s.evento, s.periodo, s.cidade_evento, s.estado_evento,
                        s.pais_evento, s.valor_solicitado, s.detalhamento, s.apresentacao]
    obrigatorios += [s.endereco.logradouro, s.endereco.numero, s.endereco.bairro,
                    s.endereco.cidade, s.endereco.estado,
                    s.pagamento.cpf, s.pagamento.rg, s.pagamento.banco,
                    s.pagamento.agencia, s.pagamento.conta]
    if any(not c.strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.pagamento.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = s.valor_solicitado
    if not valor.isdigit() or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in s.email or not s.email.split("@")[-1].strip():
        erros.append("E-mail inválido")
    import re
    if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", s.pagamento.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not validar_cpf_digitos(s.pagamento.cpf):
        erros.append("CPF inválido")
    if not re.match(r"^\d{5}-\d{3}$", s.endereco.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", s.pagamento.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            dia, mes, ano = map(int, s.pagamento.data_nascimento.split("/"))
            datetime.date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def formatar_valor_centavos(valor_solicitado: str) -> str:
    centavos = int(valor_solicitado)
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def gerar_oficio(s: Solicitacao, hoje: str) -> str:
    valor_formatado = formatar_valor_centavos(s.valor_solicitado)
    if s.aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento:
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {valor_formatado}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.endereco.logradouro}, {s.endereco.numero}",
    ]
    if s.endereco.complemento:
        linhas.append(f"Complemento: {s.endereco.complemento}")
    linhas += [
        f"CEP: {s.endereco.cep}",
        f"{s.endereco.bairro}, {s.endereco.cidade} - {s.endereco.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.pagamento.data_nascimento}",
        f"CPF: {s.pagamento.cpf}",
        f"RG / RNM: {s.pagamento.rg}",
        f"Banco: {s.pagamento.banco}",
        f"Agência: {s.pagamento.agencia}",
        f"Conta: {s.pagamento.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def processar(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    return {"ok": True, "oficio": gerar_oficio(s, hoje)}
