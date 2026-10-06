"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

A interface é conferida pelos arquivos estáticos que a aplicação serve; a validação e
o ofício, pela resposta do backend a envios feitos na rota POST da própria aplicação.
"""

import itertools
import 
import re
import unicodedata

import pytest
from fastapi.testclient import TestClient

from app import app

BLOCOS = (
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
)
SO_NA_ABA_ALUNOS = ("NÍVEL", "TIPO DE AUXÍLIO")
OPCOES = (
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
)
ROTULOS_SOLICITANTE_E_EVENTO = (
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
)
ROTULOS_ENDERECO = (
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
)
ROTULOS_PAGAMENTO = (
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
)
ROTULOS = ROTULOS_SOLICITANTE_E_EVENTO + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO


def _rotas_post():
    rotas = []
    for rota in app.routes:
        if "POST" not in (getattr(rota, "methods", None) or ""):
            continue
        caminho = rota.path
        parametros = re.findall(r"\{[^}]+\}", caminho)
        if not parametros:
            rotas.append(caminho)
            continue
        for combinacao in itertools.product(("alunos", "docentes"), repeat=len(parametros)):
            expandido = caminho
            for parametro, valor in zip(parametros, combinacao):
                expandido = expandido.replace(parametro, valor, 1)
            rotas.append(expandido)
    return rotas


ROTAS_POST = _rotas_post()


def _absoluto(caminho):
    return caminho if caminho.startswith("/") else "/" + caminho


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def pagina(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope="module")
def caminho_css(pagina):
    encontrado = re.search(r'<link[^>]+href=["\']([^"\']+\.css)', pagina, re.I)
    assert encontrado, "index.html deve vincular o style.css"
    assert encontrado.group(1).split("?")[0].endswith("style.css")
    return _absoluto(encontrado.group(1))


@pytest.fixture(scope="module")
def caminho_js(pagina):
    encontrado = re.search(r'<script[^>]+src=["\']([^"\']+\.js)', pagina, re.I)
    assert encontrado, "index.html deve carregar o app.js"
    assert encontrado.group(1).split("?")[0].endswith("app.js")
    return _absoluto(encontrado.group(1))


@pytest.fixture(scope="module")
def css(client, caminho_css):
    resposta = client.get(caminho_css)
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope="module")
def js(client, caminho_js):
    resposta = client.get(caminho_js)
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope="module")
def interface(pagina, js):
    if "NOME COMPLETO - SEM ABREVIAR" in pagina:
        return pagina
    return pagina + "\n" + js


def test_abas_alunos_e_docentes_nessa_ordem(interface):
    assert "ALUNOS" in interface
    assert "DOCENTES" in interface
    assert interface.index("ALUNOS") < interface.index("DOCENTES")


def test_blocos_com_titulo_visivel(interface):
    ausentes = [titulo for titulo in BLOCOS if titulo not in interface]
    assert not ausentes, f"blocos sem título visível: {ausentes}"


def test_rotulos_dos_campos(interface):
    ausentes = [rotulo for rotulo in ROTULOS if rotulo not in interface]
    assert not ausentes, f"rótulos ausentes: {ausentes}"


def test_campos_exclusivos_da_aba_alunos(interface):
    for rotulo in SO_NA_ABA_ALUNOS:
        assert interface.count(rotulo) == 1, f"{rotulo} só pode existir na aba ALUNOS"


def test_opcoes_das_selecoes(interface):
    ausentes = [opcao for opcao in OPCOES if opcao not in interface]
    assert not ausentes, f"opções ausentes: {ausentes}"


def test_rotulos_na_ordem_definida(interface):
    posicao = -1
    for rotulo in ROTULOS:
        posicao = interface.find(rotulo, posicao + 1)
        assert posicao != -1, f"rótulo ausente ou fora de ordem: {rotulo}"


def test_botao_enviar_solicitacao(interface):
    assert "Enviar solicitação" in interface


def test_titulo_da_confirmacao(interface):
    assert "Solicitação registrada" in interface


def test_cabecalho_institucional(interface):
    assert "usp-logo.png" in interface
    assert "Universidade de São Paulo" in interface
    assert any(
        palavra in interface
        for palavra in ("Pós-Graduação", "IME-USP", "Instituto de Matemática")
    )


def test_logo_da_usp_e_servida(client, interface):
    encontrado = re.search(r'src=["\']([^"\']*usp-logo\.png)["\']', interface, re.I)
    assert encontrado, "o cabeçalho deve usar o arquivo assets/usp-logo.png"
    resposta = client.get(_absoluto(encontrado.group(1)))
    assert resposta.status_code == 200
    assert resposta.headers.get("content-type", "").lower().startswith("image")


def test_azul_primario_da_usp_no_estilo(css):
    assert "#1094ab" in css.lower()


def test_nenhum_recurso_vem_da_rede(pagina, css, js):
    padrao = re.compile(
        r"(?:(?:src|href)\s*=\s*[\"']?\s*(?:https?:)?//"
        r"|url\(\s*[\"']?\s*(?:https?:)?//"
        r"|@import\s*[\"']?\s*https?://"
        r'|fetch\(\s*["\']\s*https?://)',
        re.I,
    )
    for texto in (pagina, css, js):
        assert not padrao.search(texto), "nenhum arquivo pode vir da rede"


def test_todo_campo_tem_placeholder_de_exemplo(interface):
    tags = re.findall(r"<(?:input|textarea)[^>]*>", interface, re.I)
    assert tags, "os formulários devem ter campos"
    rotulos = set(ROTULOS)
    for tag in tags:
        encontrado = (
            re.search(r'placeholder\s*=\s*"([^"]*)"', tag, re.I)
            or re.search(r"placeholder\s*=\s*'([^']*)'", tag, re.I)
            or re.search(r"placeholder\s*=\s*([^\s>]+)", tag, re.I)
        )
        assert encontrado, f"campo sem placeholder: {tag[:80]}"
        valor = encontrado.group(1).strip()
        assert valor, f"placeholder vazio: {tag[:80]}"
        assert valor not in rotulos, f"placeholder não deve repetir o rótulo: {valor}"


def test_texto_longo_e_selecoes(interface):
    assert re.search(r"<textarea\b", interface, re.I), (
        "o detalhamento do pedido é um campo de várias linhas"
    )
    assert re.search(r"<select\b", interface, re.I), (
        "nível, tipo de auxílio e apresentação são seleções"
    )


def _snake(rotulo):
    texto = rotulo.replace("(R$)", "")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^0-9a-zA-Z]+", "_", texto)
    return re.sub(r"_+", "_", texto).strip("_").lower()


def _camel(rotulo):
    partes = _snake(rotulo).split("_")
    return partes[0] + "".join(parte.capitalize() for parte in partes[1:])


DEFINICOES = (
    ("nome", "NOME COMPLETO - SEM ABREVIAR",
     ("nome", "nomeCompleto", "nome_completo_sem_abreviar", "nome do solicitante")),
    ("nuspu", "N. USP",
     ("nusp", "numero_usp", "numeroUSP", "numeroNusp", "codpes", "numero do usp")),
    ("programa", "PROGRAMA", ()),
    ("nivel", "NÍVEL", ()),
    ("auxilio", "TIPO DE AUXÍLIO",
     ("tipo_auxilio", "tipo_de_auxilio", "tipoAuxilio", "auxilio", "tipo")),
    ("email", "E-MAIL", ("email", "e-mail", "mail", "eMail")),
    ("evento", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
     ("evento", "nome_evento", "nome_do_evento", "nomeEvento", "nome_do_evento_ou_banca",
      "banca")),
    ("periodo", "PERÍODO DO EVENTO, EXAME OU DEFESA",
     ("periodo", "periodo_evento", "periodo_do_evento", "periodoEvento",
      "periodo_do_evento_exame_ou_defesa")),
    ("cidade_evento", "CIDADE DO EVENTO, EXAME OU DEFESA",
     ("cidade_evento", "cidade_do_evento", "cidadeEvento", "evento_cidade",
      "cidade_do_evento_exame_ou_defesa")),
    ("estado_evento", "ESTADO DO EVENTO, EXAME OU DEFESA",
     ("estado_evento", "estado_do_evento", "estadoEvento", "evento_estado",
      "estado_do_evento_exame_ou_defesa")),
    ("pais", "PAÍS DO EVENTO, EXAME OU DEFESA",
     ("pais", "pais_evento", "pais_do_evento", "paisEvento", "evento_pais",
      "pais_do_evento_exame_ou_defesa")),
    ("link", "LINK DO EVENTO, EXAME OU DEFESA",
     ("link", "link_evento", "link_do_evento", "linkEvento", "url", "site", "evento_link")),
    ("valor", "VALOR SOLICITADO (R$)", ("valor", "valor_solicitado", "valorSolicitado")),
    ("detalhamento", "DETALHAMENTO DO PEDIDO",
     ("detalhamento", "detalhamento_pedido", "detalhamento_do_pedido", "detalhamentoPedido",
      "detalhes", "descricao")),
    ("apresentacao", "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
     ("apresentacao", "apresentacao_trabalho", "apresentacao_de_trabalho",
      "ira_apresentar_trabalho", "trabalho", "apresentacaoNoEvento",
      "apresentacao_trabalho_no_evento")),
    ("nascimento", "DATA DE NASCIMENTO",
     ("data_nascimento", "data_de_nascimento", "nascimento", "dataNascimento",
      "data_de_nasc")),
    ("logradouro", "LOGRADOURO", ("logradouro", "endereco", "endereco_logradouro")),
    ("numero", "NÚMERO", ("numero", "numero_endereco", "numero_logradouro", "num")),
    ("complemento", "COMPLEMENTO", ("complemento",)),
    ("bairro", "BAIRRO", ("bairro",)),
    ("cep", "CEP", ("cep",)),
    ("cidade", "CIDADE",
     ("cidade_endereco", "cidade_solicitante", "cidade_do_solicitante", "endereco_cidade")),
    ("estado", "ESTADO",
     ("estado_endereco", "estado_solicitante", "estado_do_solicitante", "endereco_estado")),
    ("cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)", ("cpf",)),
    ("rg", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
     ("rg", "rnm", "rg_rnm", "rgRnm", "rg_rnm_separados_por_pontos_e_traco",
      "documento_identidade")),
    ("banco", "NOME DO BANCO", ("banco", "nome_banco", "nome_do_banco", "nomeBanco")),
    ("agencia", "NÚMERO DA AGÊNCIA",
     ("agencia", "numero_agencia", "numero_da_agencia", "numeroAgencia")),
    ("conta", "NÚMERO DA CONTA", ("conta", "numero_conta", "numero_da_conta", "numeroConta")),
)

CHAVES_DISCRIMINADOR = (
    "aba", "formulario", "form", "tipo_formulario", "tipo_formulário", "tipo_de_formulario",
    "tipo_solicitante", "tipo_de_solicitante", "perfil", "origem", "modalidade", "categoria",
    "tipo_solicitacao", "tipo",
)
MARCADORES_ALUNO = {"aluno": True, "eh_aluno": True, "e_aluno": True, "is_aluno": True}
MARCADORES_DOCENTE = {"docente": True, "eh_docente": True, "e_docente": True, "is_docente": True}

CHAVES = {
    sigla: list(dict.fromkeys((rotulo, rotulo.lower(), _snake(rotulo), _camel(rotulo), *extras)))
    for sigla, rotulo, extras in DEFINICOES
}

VAZIO_TOTAL = {chave: "" for chaves in CHAVES.values() for chave in chaves}
for _chave in CHAVES_DISCRIMINADOR:
    VAZIO_TOTAL[_chave] = ""


def _payload(valores, com_nivel=True, disc="alunos"):
    dados = {}
    if disc is not None:
        for chave in CHAVES_DISCRIMINADOR:
            dados[chave] = disc
        if disc.lower() == "alunos":
            dados.update(MARCADORES_ALUNO)
        elif disc.lower() == "docentes":
            dados.update(MARCADORES_DOCENTE)
    for sigla, _rotulo, _extras in DEFINICOES:
        if sigla in ("nivel", "auxilio") and not com_nivel:
            continue
        for chave in CHAVES[sigla]:
            dados[chave] = valores[sigla]
    return dados


def _normalizar(texto):
    try:
        return .dumps(.loads(texto), ensure_ascii=False)
    except ValueError:
        return texto


def _postar(client, payload):
    textos = []
    for rota in ROTAS_POST:
        for envio in ({"": payload}, {"data": payload}):
            try:
                resposta = client.post(rota, **envio)
            except Exception:
                continue
            textos.append(_normalizar(resposta.text))
    return textos


def _enviar(client, valores, com_nivel=True, disc="alunos"):
    return _postar(client, _payload(valores, com_nivel=com_nivel, disc=disc))


def _resposta_com(textos, marcador):
    for texto in textos:
        if marcador in texto:
            return texto
    return None


VALIDOS = {
    "nome": "Maria de Souza",
    "nuspu": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "evento": "Simpósio de Banco de Dados",
    "periodo": "1 a 3 de julho de 2025",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais": "Brasil",
    "link": "https://ime.usp.br/evento",
    "valor": "R$ 1.500,00",
    "detalhamento": "Passagem aérea e inscrição no evento",
    "apresentacao": "Pôster",
    "nascimento": "01/02/1980",
    "logradouro": "Rua do Anfiteatro",
    "numero": "181",
    "complemento": "Sala 222",
    "bairro": "Cidade Universitária",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "98765-4",
}

OFICIO_ALUNOS = (
    "Interessada(o): Maria de Souza - 1234567",
    "E-mail: maria@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "Evento: Simpósio de Banco de Dados",
    "Período: 1 a 3 de julho de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: https://ime.usp.br/evento",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Passagem aérea e inscrição no evento",
    "Rua do Anfiteatro, 181",
    "Complemento: Sala 222",
    "CEP: 05508-090",
    "Cidade Universitária, São Paulo - SP",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 98765-4",
    "Encaminhe-se ao Serviço Financeiro para providências",
)

ERROS_DE_FORMATO = (
    "N. USP deve conter apenas números",
    "Número da agência deve conter apenas números",
    "Valor solicitado deve ser maior que 0",
    "E-mail inválido",
    "CPF deve estar no formato 000.000.000-00",
    "CEP deve estar no formato 00000-000",
    "Data de nascimento deve estar no formato dd/mm/aaaa",
)

INVALIDOS = {
    **VALIDOS,
    "nuspu": "abc",
    "email": "abc",
    "valor": "abc",
    "nascimento": "abc",
    "cep": "abc",
    "cpf": "abc",
    "agencia": "abc",
    "link": "",
    "complemento": "",
}


def test_backend_recebe_a_solicitacao():
    assert ROTAS_POST, "deve existir uma rota POST para receber a solicitação"


def test_envio_vazio_pede_preenchimento(client):
    textos = _postar(client, {}) + _postar(client, VAZIO_TOTAL)
    assert _resposta_com(textos, "Preencha todos os campos"), (
        "envio sem nenhum dado deve receber 'Preencha todos os campos'"
    )


def test_todas_as_mensagens_de_formato_saiam_juntas(client):
    textos = _enviar(client, INVALIDOS)
    ausentes = [msg for msg in ERROS_DE_FORMATO if _resposta_com(textos, msg) is None]
    assert not ausentes, f"mensagens de erro ausentes: {ausentes}"
    completa = [texto for texto in textos if all(msg in texto for msg in ERROS_DE_FORMATO)]
    assert completa, "as mensagens que se aplicam devem sair todas juntas"
    assert "Interessada(o):" not in completa[0], "com erro, o ofício não é gerado"


def test_cpf_com_digito_verificador_errado(client):
    texto = _resposta_com(
        _enviar(client, {**VALIDOS, "cpf": "123.456.789-00"}), "CPF inválido"
    )
    assert texto, "CPF com dígito verificador errado deve dar 'CPF inválido'"
    assert "CPF deve estar no formato 000.000.000-00" not in texto
    assert "Interessada(o):" not in texto


@pytest.mark.parametrize("data", ["31/02/1980", "01/13/1980"])
def test_data_de_nascimento_inexistente(client, data):
    texto = _resposta_com(
        _enviar(client, {**VALIDOS, "nascimento": data}),
        "Data de nascimento inválida",
    )
    assert texto, f"{data} não existe e deve dar 'Data de nascimento inválida'"
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in texto
    assert "Interessada(o):" not in texto


@pytest.mark.parametrize("valor", ["0", "R$ 0,00"])
def test_valor_solicitado_zero(client, valor):
    texto = _resposta_com(
        _enviar(client, {**VALIDOS, "valor": valor}),
        "Valor solicitado deve ser maior que 0",
    )
    assert texto, "valor 0 deve dar 'Valor solicitado deve ser maior que 0'"
    assert "Interessada(o):" not in texto


def test_oficio_da_aba_alunos(client):
    textos = []
    for disc in ("alunos", None):
        textos += _enviar(client, VALIDOS, disc=disc)
        textos += _enviar(client, {**VALIDOS, "valor": "150000"}, disc=disc)
    oficio = _resposta_com(
        textos, "Assunto: Solicitação de Auxílio Financeiro - Participação em evento"
    )
    assert oficio, "o envio válido deve devolver o ofício com os dados no lugar"
    ausentes = [trecho for trecho in OFICIO_ALUNOS if trecho not in oficio]
    assert not ausentes, f"trechos ausentes do ofício: {ausentes}"
    assert "Preencha todos os campos" not in oficio


def test_oficio_da_aba_docentes(client):
    base = {
        sigla: valor
        for sigla, valor in VALIDOS.items()
        if sigla not in ("nivel", "auxilio")
    }
    textos = []
    for disc in ("docentes", "DOCENTES", "Docentes", None):
        for valores in (base, {**base, "valor": "150000"}):
            textos += _enviar(client, valores, com_nivel=False, disc=disc)
    oficio = _resposta_com(textos, "Interessada(o): Maria de Souza - 1234567")
    assert oficio, "o envio válido na aba DOCENTES deve devolver o ofício"
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Mestrado" not in oficio
    assert "Participação em evento" not in oficio


def test_linhas_de_campos_opcionais_vazios_saem_do_oficio(client):
    valores = {**VALIDOS, "link": "", "complemento": ""}
    textos = _enviar(client, valores) + _enviar(client, valores, disc=None)
    oficio = _resposta_com(
        textos, "Assunto: Solicitação de Auxílio Financeiro - Participação em evento"
    )
    assert oficio
    assert "Link do evento" not in oficio, "link vazio não pode gerar linha no ofício"
    assert "Complemento" not in oficio, "complemento vazio não pode gerar linha no ofício"
