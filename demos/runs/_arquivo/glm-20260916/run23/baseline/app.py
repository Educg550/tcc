import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação do IME-USP")


class Solicitacao(BaseModel):
    perfil: str = "alunos"
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
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
    rg_rnm: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


OBRIGATORIOS = [
    "nome", "nusp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm",
    "banco", "agencia", "conta",
]

TEMPLATE = """Interessada(o): <<NOME COMPLETO - SEM ABREVIAR>> - <<N. USP>>
E-mail: <<E-MAIL>>
Assunto: <<ASSUNTO>>
Programa: <<LINHA DO PROGRAMA>>

A CCP-<<PROGRAMA>> aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: <<NOME DO EVENTO / BANCA DE EXAME OU DEFESA>>
Período: <<PERÍODO DO EVENTO, EXAME OU DEFESA>>
Local: <<CIDADE DO EVENTO, EXAME OU DEFESA>> - <<ESTADO DO EVENTO, EXAME OU DEFESA>> - <<PAÍS DO EVENTO, EXAME OU DEFESA>>
Link do evento: <<LINK DO EVENTO, EXAME OU DEFESA>>
Apresentação de trabalho: <<IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?>>
Valor solicitado: <<VALOR SOLICITADO (R$)>>
Detalhamento: <<DETALHAMENTO DO PEDIDO>>

Endereço da(o) interessada(o)
<<LOGRADOURO>>, <<NÚMERO>>
Complemento: <<COMPLEMENTO>>
CEP: <<CEP>>
<<BAIRRO>>, <<CIDADE>> - <<ESTADO>>

Dados para pagamento
Data de nascimento: <<DATA DE NASCIMENTO>>
CPF: <<CPF (SEPARADOS POR PONTOS E TRAÇO)>>
RG / RNM: <<RG / RNM (SEPARADOS POR PONTOS E TRAÇO)>>
Banco: <<NOME DO BANCO>>
Agência: <<NÚMERO DA AGÊNCIA>>
Conta: <<NÚMERO DA CONTA>>

Encaminhe-se ao Serviço Financeiro para providências."""


def _so_digitos(texto: str) -> bool:
    return re.fullmatch(r"[0-9]+", texto) is not None


def _cpf_confere(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False

    def digito(base):
        soma = sum(d * p for d, p in zip(base, range(len(base) + 1, 1, -1)))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    return digito(digitos[:9]) == digitos[9] and digito(digitos[:10]) == digitos[10]


def validar(dados: Solicitacao) -> list:
    erros = []
    if dados.perfil == "alunos":
        obrigatorios = OBRIGATORIOS + ["nivel", "tipo_auxilio"]
    else:
        obrigatorios = OBRIGATORIOS
    if any(not getattr(dados, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if dados.nusp.strip() and not _so_digitos(dados.nusp.strip()):
        erros.append("N. USP deve conter apenas números")

    if dados.agencia.strip() and not _so_digitos(dados.agencia.strip()):
        erros.append("Número da agência deve conter apenas números")

    if dados.valor.strip():
        centavos = re.sub(r"\D", "", dados.valor)
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if dados.email.strip():
        partes = dados.email.strip().split("@")
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append("E-mail inválido")

    cpf = dados.cpf.strip()
    cpf_no_formato = re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf) is not None
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = dados.cep.strip()
    cep_no_formato = re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep) is not None
    if cep and not cep_no_formato:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.data_nascimento.strip()
    nascimento_no_formato = re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento) is not None
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not _cpf_confere(cpf):
        erros.append("CPF inválido")

    if nascimento_no_formato:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r"\D", "", valor) or 0)
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def gerar_oficio(dados: Solicitacao) -> str:
    if dados.perfil == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {dados.tipo_auxilio.strip()}"
        linha_do_programa = f"{dados.programa.strip()} - {dados.nivel.strip()}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_do_programa = dados.programa.strip()

    valores = {
        "ASSUNTO": assunto,
        "LINHA DO PROGRAMA": linha_do_programa,
        "NOME COMPLETO - SEM ABREVIAR": dados.nome.strip(),
        "N. USP": dados.nusp.strip(),
        "E-MAIL": dados.email.strip(),
        "PROGRAMA": dados.programa.strip(),
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": dados.evento.strip(),
        "PERÍODO DO EVENTO, EXAME OU DEFESA": dados.periodo.strip(),
        "CIDADE DO EVENTO, EXAME OU DEFESA": dados.cidade_evento.strip(),
        "ESTADO DO EVENTO, EXAME OU DEFESA": dados.estado_evento.strip(),
        "PAÍS DO EVENTO, EXAME OU DEFESA": dados.pais_evento.strip(),
        "LINK DO EVENTO, EXAME OU DEFESA": dados.link_evento.strip(),
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": dados.apresentacao.strip(),
        "VALOR SOLICITADO (R$)": formatar_moeda(dados.valor),
        "DETALHAMENTO DO PEDIDO": dados.detalhamento.strip(),
        "LOGRADOURO": dados.logradouro.strip(),
        "NÚMERO": dados.numero.strip(),
        "COMPLEMENTO": dados.complemento.strip(),
        "CEP": dados.cep.strip(),
        "BAIRRO": dados.bairro.strip(),
        "CIDADE": dados.cidade.strip(),
        "ESTADO": dados.estado.strip(),
        "DATA DE NASCIMENTO": dados.data_nascimento.strip(),
        "CPF (SEPARADOS POR PONTOS E TRAÇO)": dados.cpf.strip(),
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": dados.rg_rnm.strip(),
        "NOME DO BANCO": dados.banco.strip(),
        "NÚMERO DA AGÊNCIA": dados.agencia.strip(),
        "NÚMERO DA CONTA": dados.conta.strip(),
    }

    descartar = []
    if not valores["LINK DO EVENTO, EXAME OU DEFESA"]:
        descartar.append("<<LINK DO EVENTO, EXAME OU DEFESA>>")
    if not valores["COMPLEMENTO"]:
        descartar.append("<<COMPLEMENTO>>")

    linhas = [
        linha for linha in TEMPLATE.split("\n")
        if not any(marcador in linha for marcador in descartar)
    ]
    oficio = "\n".join(linhas)
    for marcador, valor in valores.items():
        oficio = oficio.replace("<<" + marcador + ">>", valor)
    return oficio


@app.post("/solicitacao")
def receber_solicitacao(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados)}


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


app.mount("/", StaticFiles(directory=BASE), name="estaticos")
