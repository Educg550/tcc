import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Oficio(BaseModel):
    aba: str

    nome: str
    nusp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    evento_nome: str
    evento_periodo: str
    evento_cidade: str
    evento_estado: str
    evento_pais: str
    evento_link: Optional[str] = None
    valor: str
    detalhamento: str
    apresentacao: str

    nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cep: str
    cidade: str
    estado: str

    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


CAMPOS_OBRIGATORIOS = [
    "nome", "nusp", "programa", "email", "evento_nome", "evento_periodo",
    "evento_cidade", "evento_estado", "evento_pais", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def _digitos(texto):
    return re.sub(r"\D", "", texto or "")


def _cpf_ok(cpf):
    d = _digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for i in range(2):
        soma = sum(int(d[j]) * (len(d) - j) for j in range(len(d) - 1 - i))
        if int(d[len(d) - 2 + i]) != (11 - soma % 11) % 10:
            return False
    return True


def _valor_ok(valor):
    d = _digitos(valor)
    if not d or d != valor:
        return False
    try:
        return int(d) > 0
    except ValueError:
        return False


def valida(oficio):
    erros = []

    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if oficio.aba == "ALUNOS":
        obrigatorios += ["nivel", "tipo_auxilio"]

    vazio = any(not getattr(oficio, campo) for campo in obrigatorios)

    if vazio:
        erros.append("Preencha todos os campos")
    if not oficio.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not oficio.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if not _valor_ok(oficio.valor):
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in oficio.email or oficio.email.rsplit("@", 1)[1].count(".") < 1:
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", oficio.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_ok(oficio.cpf):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", oficio.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", oficio.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not _data_existe(oficio.nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def _data_existe(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def _moeda(valor):
    inteiro = valor.rstrip(",0") or "0"
    if not inteiro.isdigit():
        return valor
    d = "".join("0" if len(inteiro) < 3 else inteiro)
    if len(inteiro) < 3:
        d = inteiro + "0" * (3 - len(inteiro))
    inteiro = ""
    for i, c in enumerate(reversed(d)):
        if i and i % 3 == 0:
            inteiro = "." + inteiro
        inteiro = c + inteiro
    return f"R${inteiro},{d[-2:]}"


def _linha(rotulo, valor):
    if not valor:
        return None
    return f"{rotulo}{valor}"


def oficio_comum(oficio):
    corpo = []
    corpo.append(f"Interessada(o): {oficio.nome} - {oficio.nusp}")
    corpo.append(f"E-mail: {oficio.email}")
    corpo.append(f"Assunto: Solicitação de Auxílio Financeiro - {_assunto(oficio)}")
    corpo.append(f"Programa: {oficio.programa}{_nivel(oficio)}")
    corpo.append("")
    corpo.append("A CCP-" + oficio.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    corpo.append("interessada(o) acima, conforme segue:")
    corpo.append("")
    corpo.append("Dados do evento")
    corpo.append(f"Evento: {oficio.evento_nome}")
    corpo.append(f"Período: {oficio.evento_periodo}")
    corpo.append(f"Local: {oficio.evento_cidade} - {oficio.evento_estado} - {oficio.evento_pais}")
    corpo.append(_linha("Link do evento: ", oficio.evento_link) or "")
    corpo.append(f"Apresentação de trabalho: {oficio.apresentacao}")
    corpo.append(f"Valor solicitado: {_moeda(oficio.valor)}")
    corpo.append(f"Detalhamento: {oficio.detalhamento}")
    corpo.append("")
    corpo.append("Endereço da(o) interessada(o)")
    corpo.append(f"{oficio.logradouro}, {oficio.numero}")
    corpo.append(_linha("Complemento: ", oficio.complemento) or "")
    corpo.append(f"CEP: {oficio.cep}")
    corpo.append(f"{oficio.bairro}, {oficio.cidade} - {oficio.estado}")
    corpo.append("")
    corpo.append("Dados para pagamento")
    corpo.append(f"Data de nascimento: {oficio.nascimento}")
    corpo.append(f"CPF: {oficio.cpf}")
    corpo.append(f"RG / RNM: {oficio.rg}")
    corpo.append(f"Banco: {oficio.banco}")
    corpo.append(f"Agência: {oficio.agencia}")
    corpo.append(f"Conta: {oficio.conta}")
    corpo.append("")
    corpo.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(corpo)


def _assunto(oficio):
    return oficio.tipo_auxilio or "Verba do programa"


def _nivel(oficio):
    return f" - {oficio.nivel}" if oficio.nivel else ""


def oficio_docente(oficio):
    return oficio_comum(oficio)


def oficio_aluno(oficio):
    return oficio_comum(oficio)
