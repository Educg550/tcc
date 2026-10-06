import 
import re
import sys
import unicodedata
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app

FIM_DO_OFICIO = "Encaminhe-se ao Serviço Financeiro para providências"

VALORES = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria de Souza Silva",
    "N. USP": "8765432",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria.souza@usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Simpósio Brasileiro de Banco de Dados",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "22 a 25 de setembro de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "Campinas",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://sbbd.org.br/2025",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Passagem aérea e inscrição no evento.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Anfiteatro",
    "NÚMERO": "155",
    "COMPLEMENTO": "Sala 10",
    "BAIRRO": "Cidade Universitária",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "98765-4",
}

# nomes de campo plausíveis para cada rótulo, do mais específico ao mais genérico
CANDIDATOS = {
    "N. USP": ["n_usp", "nusp", "numero_usp", "num_usp", "nro_usp"],
    "NÍVEL": ["nivel"],
    "TIPO DE AUXÍLIO": ["tipo_auxilio", "tipo_de_auxilio", "tipoauxilio", "auxilio", "tipo"],
    "E-MAIL": ["email", "e_mail", "mail"],
    "CIDADE DO EVENTO, EXAME OU DEFESA": ["cidade_evento", "cidade_do_evento"],
    "ESTADO DO EVENTO, EXAME OU DEFESA": ["estado_evento", "estado_do_evento", "uf_evento"],
    "PAÍS DO EVENTO, EXAME OU DEFESA": ["pais_evento", "pais_do_evento"],
    "LINK DO EVENTO, EXAME OU DEFESA": [
        "link_evento", "link_do_evento", "url_evento", "site_evento", "link", "url",
    ],
    "PERÍODO DO EVENTO, EXAME OU DEFESA": ["periodo_evento", "periodo_do_evento", "periodo"],
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": [
        "nome_evento", "nome_do_evento", "evento", "nome_evento_banca",
    ],
    "VALOR SOLICITADO (R$)": ["valor_solicitado", "valor", "valor_reais", "valor_em_reais"],
    "DETALHAMENTO DO PEDIDO": [
        "detalhamento", "detalhamento_do_pedido", "detalhamento_pedido", "descricao", "observacoes",
    ],
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": [
        "apresentacao_trabalho", "apresentacao", "apresentar_trabalho", "tipo_apresentacao",
        "apresentacao_trabalho_evento", "ira_apresentar_trabalho", "trabalho", "apresenta",
    ],
    "DATA DE NASCIMENTO": [
        "data_nascimento", "data_de_nascimento", "nascimento", "datanascimento",
    ],
    "NÚMERO DA AGÊNCIA": ["numero_agencia", "num_agencia", "agencia"],
    "NÚMERO DA CONTA": ["numero_conta", "num_conta", "conta"],
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": ["cpf", "numero_cpf", "cpf_solicitante"],
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": [
        "rg_rnm", "rg", "rnm", "rg_ou_rnm", "documento_identidade",
    ],
    "NOME DO BANCO": ["nome_banco", "nome_do_banco", "banco"],
    "LOGRADOURO": ["logradouro", "endereco", "rua"],
    "NÚMERO": ["numero", "numero_endereco", "numero_logradouro", "num_endereco"],
    "COMPLEMENTO": ["complemento", "complemento_endereco"],
    "BAIRRO": ["bairro"],
    "CEP": ["cep"],
    "CIDADE": ["cidade_solicitante", "cidade_endereco", "cidade_interessado", "cidade"],
    "ESTADO": ["estado_solicitante", "estado_endereco", "estado_interessado", "estado", "uf"],
    "PROGRAMA": ["programa", "nome_programa", "programa_pos", "programa_pos_graduacao"],
    "NOME COMPLETO - SEM ABREVIAR": [
        "nome_completo", "nomecompleto", "nome", "nome_solicitante", "nome_do_solicitante",
        "nome_interessado", "nome_aluno", "nome_docente",
    ],
}

_FRACAS = {"de", "do", "da", "dos", "das", "por", "e", "no", "na", "em", "ou", "que", "sem"}
_TAB = ("aba", "tab", "perfil", "origem", "formulario", "categoria", "modo", "papel", "tipo", "classe")


def _juntar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", texto)
    partes = re.sub(r"[^A-Za-z0-9]+", " ", texto).lower().split()
    return "".join(partes)


def _conteudo(rotulo):
    texto = unicodedata.normalize("NFKD", rotulo)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    partes = re.sub(r"[^A-Za-z0-9]+", " ", texto).lower().split()
    return [p for p in partes if p not in _FRACAS and len(p) >= 2]


def _prefixo_comum(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _nota(rotulo, pj):
    tokens = _conteudo(rotulo)
    if not pj or not tokens:
        return 0.0
    acertos = 0
    for t in tokens:
        if t in pj or (len(t) >= 6 and _prefixo_comum(t, pj) >= 6):
            acertos += 1
    nota = acertos / len(tokens)
    j = _juntar(rotulo)
    if (len(pj) >= 4 and pj in j) or (len(j) >= 4 and j in pj):
        nota += 0.3
    return nota


def _forte(rotulo, pj):
    return any(len(t) >= 6 and _prefixo_comum(t, pj) >= 7 for t in _conteudo(rotulo))


def _parece_tab(nome):
    pj = _juntar(nome)
    return any(k in pj for k in _TAB)


def _mapear(nomes):
    mapa = {}
    usados = set()
    for rotulo, candidatos in CANDIDATOS.items():
        for candidato in candidatos:
            cj = _juntar(candidato)
            for caminho, pj in nomes.items():
                if caminho in usados:
                    continue
                if cj == pj or (len(cj) >= 5 and cj in pj) or (len(pj) >= 5 and pj in cj):
                    mapa[rotulo] = caminho
                    usados.add(caminho)
                    break
            if rotulo in mapa:
                break
    for rotulo in CANDIDATOS:
        if rotulo in mapa:
            continue
        melhor, nota_melhor, forte_melhor = None, 0.0, False
        for caminho, pj in nomes.items():
            if caminho in usados:
                continue
            nota = _nota(rotulo, pj)
            forte = _forte(rotulo, pj)
            if nota > nota_melhor or (nota == nota_melhor and forte and not forte_melhor):
                melhor, nota_melhor, forte_melhor = caminho, nota, forte
        if melhor is not None and (nota_melhor >= 0.6 or forte_melhor):
            mapa[rotulo] = melhor
            usados.add(melhor)
    return mapa


def _props_de(spec, esquema):
    esquema = esquema or {}
    if "$ref" in esquema:
        nome = esquema["$ref"].split("/")[-1]
        modelo = spec.get("components", {}).get("schemas", {}).get(nome, {}) or {}
        return modelo.get("properties", {}) or {}
    return esquema.get("properties", {}) or {}


def _props_raiz(spec, esquema):
    props = {}
    for chave in ("allOf", "anyOf", "oneOf"):
        for sub in (esquema or {}).get(chave, []) or []:
            props.update(_props_raiz(spec, sub))
    props.update(_props_de(spec, esquema))
    return props


def _folhas(spec, props, prefixo=()):
    folhas = {}
    for nome, esquema in props.items():
        caminho = prefixo + (nome,)
        if (esquema or {}).get("type") == "object" or "$ref" in (esquema or {}):
            subs = _props_de(spec, esquema)
            if subs:
                folhas.update(_folhas(spec, subs, caminho))
                continue
        folhas[caminho] = esquema or {}
    return folhas


def _corpo_da_rota(operacao):
    conteudos = ((operacao.get("requestBody") or {}).get("content") or {})
    for tipo in ("application/", "multipart/form-data", "application/x-www-form-urlencoded"):
        if tipo in conteudos:
            return tipo, conteudos[tipo].get("schema", {}) or {}
    if conteudos:
        tipo = sorted(conteudos)[0]
        return tipo, conteudos[tipo].get("schema", {}) or {}
    return "application/", {}


def _coagir(valor, esquema):
    tipo = (esquema or {}).get("type", "string")
    if tipo in ("integer", "number"):
        digitos = re.sub(r"\D", "", str(valor))
        if not digitos:
            return 0
        return float(digitos) if tipo == "number" else int(digitos)
    return valor


def _definir(payload, caminho, valor):
    alvo = payload
    for parte in caminho[:-1]:
        alvo = alvo.setdefault(parte, {})
    alvo[caminho[-1]] = valor


def _obter(payload, caminho):
    alvo = payload
    for parte in caminho:
        if not isinstance(alvo, dict) or parte not in alvo:
            return None
        alvo = alvo[parte]
    return alvo


def _remover(payload, caminho):
    alvo = payload
    for parte in caminho[:-1]:
        if not isinstance(alvo, dict) or parte not in alvo:
            return
        alvo = alvo[parte]
    if isinstance(alvo, dict):
        alvo.pop(caminho[-1], None)


def _montar(rota, tab, sobrescrever=None):
    payload = {}
    for rotulo, caminho in rota["mapa"].items():
        valor = VALORES[rotulo]
        if sobrescrever and rotulo in sobrescrever:
            valor = sobrescrever[rotulo]
        _definir(payload, caminho, _coagir(valor, rota["folhas"].get(caminho, {})))
    for caminho, esquema in rota["folhas"].items():
        if _obter(payload, caminho) is not None:
            continue
        if len(caminho) == 1 and _parece_tab(caminho[0]):
            _definir(payload, caminho, tab)
        elif (esquema or {}).get("type") in ("integer", "number"):
            _definir(payload, caminho, 0)
        else:
            _definir(payload, caminho, "")
    return payload


def _achatar(payload, prefixo=""):
    saida = {}
    for chave, valor in payload.items():
        caminho = f"{prefixo}{chave}"
        if isinstance(valor, dict):
            saida.update(_achatar(valor, caminho + "."))
        else:
            saida[caminho] = "" if valor is None else str(valor)
    return saida


def _enviar(client, rota, payload):
    if rota["tipo"] == "application/":
        return client.post(rota["caminho"], =payload)
    return client.post(rota["caminho"], data=_achatar(payload))


def _texto(resposta):
    try:
        return .dumps(resposta.(), ensure_ascii=False)
    except Exception:
        return resposta.text


def _plano(texto):
    return re.sub(r"\s+", " ", texto.replace("\\n", " ").replace("\\r", " ").replace("\\t", " "))


def _e_oficio(resposta):
    texto = _texto(resposta)
    return "Interessada(o):" in texto and FIM_DO_OFICIO in texto


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def spec(client):
    resposta = client.get("/openapi.")
    assert resposta.status_code == 200, "openapi. não está disponível"
    return resposta.()


@pytest.fixture(scope="module")
def rotas(spec):
    preparadas = []
    for caminho, operacoes in spec.get("paths", {}).items():
        for metodo, operacao in operacoes.items():
            if str(metodo).lower() != "post":
                continue
            tipo, esquema = _corpo_da_rota(operacao)
            props = _props_raiz(spec, esquema)
            if not props:
                continue
            folhas = _folhas(spec, props)
            nomes = {c: _juntar(c[-1]) for c in folhas}
            rota = {
                "caminho": caminho,
                "tipo": tipo,
                "folhas": folhas,
                "mapa": _mapear(nomes),
            }
            rota["tem_nivel"] = "NÍVEL" in rota["mapa"]
            preparadas.append(rota)
    return preparadas


def test_existe_rota_para_receber_a_solicitacao(rotas):
    assert rotas, "o backend não expõe rota POST para receber a solicitação"


@pytest.fixture(scope="module")
def base(client, rotas):
    ordenadas = sorted(rotas, key=lambda r: not r["tem_nivel"])
    for rota in ordenadas:
        for tab in ("alunos", "aluno", ""):
            for valor in ("R$ 1.500,00", "150000"):
                payload = _montar(rota, tab, sobrescrever={"VALOR SOLICITADO (R$)": valor})
                resposta = _enviar(client, rota, payload)
                if _e_oficio(resposta):
                    return {"rota": rota, "payload": payload, "resposta": resposta, "rotas": ordenadas}
    pytest.fail("nenhum envio com dados válidos produziu o ofício")


def _resposta_com(client, base, mudancas):
    rota = base["rota"]
    payload = .loads(.dumps(base["payload"]))
    for rotulo, valor in mudancas.items():
        caminho = rota["mapa"].get(rotulo)
        if caminho is None:
            pytest.skip(f"campo não identificado no backend: {rotulo}")
        _definir(payload, caminho, _coagir(valor, rota["folhas"].get(caminho, {})))
    return _enviar(client, rota, payload)


def test_oficio_alunos_com_dados_no_lugar(base):
    texto = _plano(_texto(base["resposta"]))
    assert "Mestrado" in texto
    assert re.search(r"Interessada\(o\):\s*Maria de Souza Silva\s*-\s*8765432", texto)
    assert re.search(r"E-mail:\s*maria\.souza@usp\.br", texto)
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "A CCP-Ciência da Computação aprovou" in texto
    assert "Dados do evento" in texto
    assert "Evento: Simpósio Brasileiro de Banco de Dados" in texto
    assert "Período: 22 a 25 de setembro de 2025" in texto
    assert "Local: Campinas - SP - Brasil" in texto
    assert "Link do evento: https://sbbd.org.br/2025" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Passagem aérea e inscrição no evento." in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert re.search(r"Rua do Anfiteatro,\s*155", texto)
    assert "Complemento: Sala 10" in texto
    assert "CEP: 05508-090" in texto
    assert "Cidade Universitária, São Paulo - SP" in texto
    assert "Dados para pagamento" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 98765-4" in texto
    assert FIM_DO_OFICIO in texto
    assert "<<" not in texto
    assert ">>" not in texto


def test_oficio_docentes_tem_verba_do_programa(client, base):
    candidato = None
    tentativas = [base["rota"]] + [r for r in base["rotas"] if r is not base["rota"]]
    for rota in tentativas:
        if rota is base["rota"]:
            modelo = .loads(.dumps(base["payload"]))
        else:
            modelo = _montar(rota, "docentes")
        variantes = []
        for tirar in (True, False):
            parcial = .loads(.dumps(modelo))
            if tirar:
                for rotulo in ("NÍVEL", "TIPO DE AUXÍLIO"):
                    caminho = rota["mapa"].get(rotulo)
                    if caminho is not None:
                        _remover(parcial, caminho)
            for tab in ("docentes", "docente"):
                variante = .loads(.dumps(parcial))
                for caminho in rota["folhas"]:
                    if len(caminho) == 1 and _parece_tab(caminho[0]):
                        _definir(variante, caminho, tab)
                variantes.append(variante)
        for variante in variantes:
            resposta = _enviar(client, rota, variante)
            texto = _plano(_texto(resposta))
            if "Verba do programa" in texto and FIM_DO_OFICIO in texto:
                candidato = texto
                break
        if candidato is not None:
            break
    assert candidato is not None, "ofício de docentes não foi gerado"
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in candidato
    assert "Programa: Ciência da Computação" in candidato
    assert re.search(r"Interessada\(o\):\s*Maria de Souza Silva\s*-\s*8765432", candidato)
    assert "Mestrado" not in candidato
    assert "Participação em evento" not in candidato


def test_linhas_opcionais_saem_do_oficio_quando_vazias(client, base):
    resposta = _resposta_com(
        client,
        base,
        {"LINK DO EVENTO, EXAME OU DEFESA": "", "COMPLEMENTO": ""},
    )
    texto = _plano(_texto(resposta))
    assert _e_oficio(resposta)
    assert "Link do evento" not in texto
    assert "Complemento" not in texto
    assert "CEP: 05508-090" in texto
    assert "Local: Campinas - SP - Brasil" in texto


def test_envio_vazio_pede_preencher_todos_os_campos(client, base):
    rota = base["rota"]
    vazio = {}
    for caminho, esquema in rota["folhas"].items():
        valor = ""
        if (esquema or {}).get("type") in ("integer", "number"):
            valor = 0
        _definir(vazio, caminho, valor)
    resposta = _enviar(client, rota, vazio)
    texto = _plano(_texto(resposta))
    assert "Preencha todos os campos" in texto
    assert FIM_DO_OFICIO not in texto


def test_n_usp_aceita_apenas_numeros(client, base):
    resposta = _resposta_com(client, base, {"N. USP": "8765a432"})
    texto = _plano(_texto(resposta))
    assert "N. USP deve conter apenas números" in texto
    assert FIM_DO_OFICIO not in texto


def test_agencia_aceita_apenas_numeros(client, base):
    resposta = _resposta_com(client, base, {"NÚMERO DA AGÊNCIA": "12a4"})
    texto = _plano(_texto(resposta))
    assert "Número da agência deve conter apenas números" in texto
    assert FIM_DO_OFICIO not in texto


def test_valor_solicitado_deve_ser_maior_que_zero(client, base):
    vistos = []
    for valor in ("R$ 0,00", "0"):
        resposta = _resposta_com(client, base, {"VALOR SOLICITADO (R$)": valor})
        texto = _plano(_texto(resposta))
        if "Valor solicitado deve ser maior que 0" in texto:
            assert FIM_DO_OFICIO not in texto
            return
        vistos.append(texto[:200])
    pytest.fail(f"valor 0 não foi rejeitado: {vistos}")


def test_email_invalido(client, base):
    resposta = _resposta_com(client, base, {"E-MAIL": "maria.souza.usp.br"})
    texto = _plano(_texto(resposta))
    assert "E-mail inválido" in texto
    assert FIM_DO_OFICIO not in texto


def test_cpf_fora_do_formato(client, base):
    resposta = _resposta_com(client, base, {"CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909"})
    texto = _plano(_texto(resposta))
    assert "CPF deve estar no formato 000.000.000-00" in texto
    assert FIM_DO_OFICIO not in texto


def test_cep_fora_do_formato(client, base):
    resposta = _resposta_com(client, base, {"CEP": "05508090"})
    texto = _plano(_texto(resposta))
    assert "CEP deve estar no formato 00000-000" in texto
    assert FIM_DO_OFICIO not in texto


def test_data_de_nascimento_fora_do_formato(client, base):
    resposta = _resposta_com(client, base, {"DATA DE NASCIMENTO": "01021980"})
    texto = _plano(_texto(resposta))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in texto
    assert FIM_DO_OFICIO not in texto


def test_cpf_com_digito_verificador_invalido(client, base):
    resposta = _resposta_com(client, base, {"CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-00"})
    texto = _plano(_texto(resposta))
    assert "CPF inválido" in texto
    assert "deve estar no formato" not in texto
    assert FIM_DO_OFICIO not in texto


def test_data_de_nascimento_inexistente(client, base):
    resposta = _resposta_com(client, base, {"DATA DE NASCIMENTO": "31/02/1980"})
    texto = _plano(_texto(resposta))
    assert "Data de nascimento inválida" in texto
    assert "deve estar no formato" not in texto
    assert FIM_DO_OFICIO not in texto


def test_todas_as_mensagens_de_erro_aparecem_juntas(client, base):
    resposta = _resposta_com(
        client,
        base,
        {
            "N. USP": "8765a432",
            "NÚMERO DA AGÊNCIA": "12a4",
            "VALOR SOLICITADO (R$)": "R$ 0,00",
            "E-MAIL": "maria.souza.usp.br",
            "CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909",
            "CEP": "05508090",
            "DATA DE NASCIMENTO": "01021980",
        },
    )
    texto = _plano(_texto(resposta))
    for mensagem in (
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert mensagem in texto
    assert "Preencha todos os campos" not in texto
    assert FIM_DO_OFICIO not in texto
