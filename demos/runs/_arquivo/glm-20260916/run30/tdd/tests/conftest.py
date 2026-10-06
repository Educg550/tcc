'''Infraestrutura dos testes e contrato HTTP da aplicação.

Contrato exercitado por estes testes:

- A aplicação FastAPI está exposta como ``app`` no módulo ``app`` da raiz do
  projeto (o mesmo objeto que ``uvicorn app:app`` serve).
- ``GET /`` devolve a página do formulário; ``/style.css``, ``/app.js`` e
  ``/assets/usp-logo.png`` são servidos como arquivos estáticos.
- A solicitação é enviada por ``POST`` com corpo JSON ao endpoint de
  solicitação. Os nomes dos campos seguem os rótulos da tela, em minúsculas e
  sem acento, e o campo ``aba`` vale ``'alunos'`` ou ``'docentes'`` e define
  qual dos dois ofícios é gerado.
- Resposta aceita: contém o ofício redigido, com os dados no lugar dos
  marcadores, preservando as quebras de linha.
- Resposta rejeitada: contém as mensagens de erro que se aplicam.
'''

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app import app  # noqa: E402

ROTAS_CANDIDATAS = [
    '/api/solicitacao',
    '/solicitacao',
    '/api/solicitacoes',
    '/solicitar',
    '/api/auxilio',
    '/auxilio',
    '/api/enviar',
    '/enviar',
    '/api/submit',
    '/submit',
]


def _payload(aba):
    return {
        'aba': aba,
        'nome_completo': 'Maria Antonieta da Silva',
        'n_usp': '8765432',
        'programa': 'Ciência da Computação',
        'nivel': 'Mestrado',
        'tipo_auxilio': 'Participação em evento',
        'email': 'maria.antonieta@usp.br',
        'nome_evento': 'Simpósio Internacional de Banco de Dados',
        'periodo_evento': '10/03/2026 a 14/03/2026',
        'cidade_evento': 'Rio de Janeiro',
        'estado_evento': 'RJ',
        'pais_evento': 'Brasil',
        'link_evento': 'https://simposio.example.org',
        'valor_solicitado': 'R$ 1.500,00',
        'detalhamento': 'Passagem aérea e inscrição no evento.',
        'apresentacao': 'Pôster',
        'data_nascimento': '01/02/1980',
        'logradouro': 'Rua do Anfiteatro',
        'numero': '101',
        'complemento': 'Sala 12',
        'bairro': 'Cidade Universitária',
        'cep': '05508-090',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'cpf': '123.456.789-09',
        'rg_rnm': '12.345.678-9',
        'banco': 'Banco do Brasil',
        'agencia': '1234',
        'conta': '98765-4',
    }


def _strings(conteudo):
    if isinstance(conteudo, str):
        yield conteudo
    elif isinstance(conteudo, dict):
        for valor in conteudo.values():
            yield from _strings(valor)
    elif isinstance(conteudo, (list, tuple)):
        for valor in conteudo:
            yield from _strings(valor)


@pytest.fixture(scope='session')
def client():
    return TestClient(app)


@pytest.fixture(scope='session')
def rota(client):
    for candidata in ROTAS_CANDIDATAS:
        resposta = client.post(candidata, =_payload('alunos'))
        if resposta.status_code not in (404, 405):
            return candidata
    pytest.fail(
        'nenhum endpoint aceitou o POST da solicitação (esperado um endpoint '
        'que valide o formulário e devolva o ofício)'
    )


@pytest.fixture
def payload_alunos():
    return _payload('alunos')


@pytest.fixture
def payload_docentes():
    payload = _payload('docentes')
    del payload['nivel']
    del payload['tipo_auxilio']
    return payload


@pytest.fixture
def enviar(client, rota):
    def _enviar(payload):
        return client.post(rota, =payload)

    return _enviar


@pytest.fixture
def mensagens():
    def _mensagens(resposta):
        try:
            corpo = resposta.()
        except ValueError:
            corpo = resposta.text
        linhas = []
        for texto in _strings(corpo):
            linhas.extend(linha.strip() for linha in texto.splitlines() if linha.strip())
        return linhas

    return _mensagens


@pytest.fixture
def oficio():
    def _oficio(resposta):
        try:
            corpo = resposta.()
        except ValueError:
            texto = resposta.text
        else:
            texto = '\n'.join(t for t in _strings(corpo) if 'Interessada(o):' in t)
        return texto.replace('\r\n', '\n').replace('\r', '\n')

    return _oficio
