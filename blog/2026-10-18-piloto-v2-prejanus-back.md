---
slug: piloto-v2-prejanus-back
title: "Piloto v2: o backend inteiro do PreJanus e o gargalo da escrita de arquivos"
authors: [eduardo]
tags: [tcc, experimento]
---

Ampliei o piloto do Caronte da consulta para o prejanus-back inteiro: 50 operações,
dois bancos, Senha Única, SMTP e relatórios. Rodei os três grupos primeiro no OpenCode
e depois no harness antigo, em Agno. Nenhuma entrega chegou a subir de forma útil, e
a causa que sobrou no fim é a forma como o agente escreve arquivos, não o escopo.

<!-- truncate -->

## O que mudou do v1 para o v2

O requisito passou a ter 33 itens, cobrindo as 50 operações do OpenAPI original. A
avaliação roda num ambiente Docker próprio com o Forms, o Front, o proxy, um provedor
OAuth local que imita o contrato da USP e um SMTP local. O backend candidato entra no
lugar dos três serviços de backend do original, e o resto continua sendo o sistema
original.

O gabarito tem 247 casos e exercita as 50 operações. No original, 233 passam. Os 14 que
falham são dez divergências do próprio original que reproduzi por HTTP: a issue 26,
o PPI mapeado, a nota do POSCOMP, `include_comments`, `send-accept` e `send-letter`
quebrando sempre, aceite pendente aparecendo como respondido, aprovação com vários
orientadores, cadastro OAuth com papel `TEACHER` e e-mails vazios no relatório. Decidi
manter esses testes exigindo o que o requisito pede. O split ficou em 161 casos
visíveis e 85 reservados, por função de teste e estratificado por requisito.

## As tentativas no OpenCode

O primeiro baseline terminou sem código. O GLM-5.3 gastou 32.000 tokens raciocinando
num único passo, bateu no teto de saída e a sessão acabou. Esse teto era do próprio
OpenCode (`OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX`), não do modelo nem do provedor.

O segundo baseline gerou 3.237 linhas e passou em 33 dos 247 casos. Investigando, achei
duas lacunas minhas na entrada: os esquemas SQL do original não estavam em `infra/`, e
o contrato de dados do usuário da Senha Única não estava escrito em lugar nenhum. O
modelo inventou tabelas e leu o NUSP do lugar errado. Como cada teste do gabarito faz
login, quase tudo caiu junto. O terceiro baseline, já com a entrada corrigida, voltou a
bater no teto de 32k. Guardei as três como tentativas inválidas.

## As runs no Agno

Voltei para o harness em Agno numa branch, para testar de fato a hipótese que tinha
motivado a troca: a de que ele seria fraco em sessões longas. Mantive o mesmo modelo,
a mesma amostragem, as mesmas skills por etapa e o mesmo ambiente. Precisei de três
ajustes para que as runs fossem comparáveis: limitar o raciocínio a 32k tokens por
chamada (sem isso o test-writer gastava os 100k do teto só pensando e devolvia uma
resposta vazia), colocar os anexos de texto de `infra/` no prompt (o agente Agno não lê
arquivos) e fazer o proxy resolver os backends a cada requisição.

| Grupo | Duração | Custo (USD) | Passos | Pytest do gate | Gabarito |
|---|---:|---:|---:|---|---:|
| Baseline | 256 s | 0,060662 | 1 | — | app não sobe |
| TDD | 4.909 s | 0,695640 | 1 + 9 | 0/35 no fim | 2/247 |
| Rework | 6.485 s | 0,265139 | 2 | 1/161 visíveis | 2/247 |

Nos três a entrega final tem um `SyntaxError` e o servidor nem inicia. A avaliação do
baseline foi interrompida por isso, já sabendo que nenhum caso que dependa da API podia
passar. Os dois casos que passam no TDD e no rework são o rastreio dos requisitos e a
recusa de CORS para origem desconhecida, que passa com qualquer resposta sem o
cabeçalho.

O TDD mostra bem o problema. O coder chegou a 33 de 34 dos próprios testes no segundo
passo. No passo seguinte caiu para 0 de 35, voltou para 32, caiu de novo, e terminou
pelo tempo num estado quebrado. No Agno cada passo é uma chamada sem histórico: o modelo
recebe o requisito, os testes e a saída do pytest, mas não o código que escreveu, e
devolve cada arquivo inteiro como uma string dentro de um JSON. Arquivos de 1.500 a
2.300 linhas reescritos do zero a cada falha acabam quebrando em algum ponto.

## O que fica

Os dois executores esbarraram em problemas de ferramenta antes de mostrar qualquer
limite do modelo: o OpenCode no teto interno de saída, o Agno no mecanismo de escrita.
Não volto para o OpenCode. A próxima tarefa é refazer a escrita de arquivos do harness,
com leitura do projeto, edição por trecho em vez de reescrita integral, o código atual
visível entre passos e checagem de sintaxe antes de aceitar a mudança. Depois rodo os
três grupos de novo nas mesmas condições.

Há também um limite de infraestrutura: com o Docker lento depois de uma queda de luz,
cada gate do rework levava cerca de 25 minutos, e esse tempo entra no teto de uma hora
da etapa. Isso deixou o rework com só dois passos. Antes da próxima rodada preciso
deixar o `restaurar` entre testes mais barato ou tirar o tempo do gate do orçamento.

O piloto v2 custou US$ 2,45 registrados: US$ 0,84 nas três tentativas no OpenCode e
US$ 1,62 no Agno, incluindo duas runs de TDD interrompidas quando achei problemas no
meio delas. Somado ao v1, o piloto está em US$ 3,20, abaixo do teto de US$ 10.

## RUN.log das execuções no Agno

<details>
<summary>Baseline</summary>

```json
{
  "started_at": "2026-10-18T16:59:48",
  "ended_at": "2026-10-18T17:04:04",
  "total_duration_s": 256.13,
  "grupo": "baseline",
  "requisito_id": "03-caronte-prejanus-completo",
  "alvo": {
    "comando_app": "uvicorn app:app --host 0.0.0.0 --port {porta}",
    "comando_teste": "pytest -q --tb=short",
    "comando_frontend": "",
    "python": "3.11",
    "pacotes": [
      "pytest==9.0.3",
      "fastapi==0.114.2",
      "uvicorn==0.30.6",
      "sqlalchemy[asyncio]==2.0.43",
      "psycopg[c]==3.2.9",
      "pydantic==2.11.7",
      "pydantic-settings==2.10.1",
      "python-multipart==0.0.17",
      "itsdangerous==2.2.0",
      "httpx==0.27.2",
      "requests==2.32.5",
      "oauthlib==3.3.1",
      "senhaunicapy @ git+https://gitlab.com/ccsl-usp/poscomp-ime/senhaunicapy.git@db099c3532eda31ab6257030ef298290fce59e78",
      "fastapi-mail==1.5.0",
      "email-validator==2.3.0",
      "fpdf2==2.8.4",
      "matplotlib==3.10.7",
      "pypdf==6.1.3",
      "babel==2.17.0",
      "alembic==1.16.5",
      "argon2-cffi==23.1.0"
    ],
    "modelos": {
      "test_writer": "z-ai/glm-5.3",
      "coder": "z-ai/glm-5.3"
    },
    "amostragem": {
      "temperature": 0.1,
      "top_p": 0.9
    }
  },
  "orcamento": {
    "passos": 40,
    "custo_usd": 2.0,
    "tempo_s": 3600
  },
  "total_cost_usd": 0.060662,
  "total_tokens": 79632,
  "total_retries": 0,
  "stages": [
    {
      "id": "direto",
      "configured_model": "z-ai/glm-5.3",
      "duration_s": 161.54,
      "ok": true,
      "motivo": "verde",
      "passos": 1,
      "retries": 0,
      "arquivos": [
        "app.py"
      ],
      "historico": [],
      "input_tokens": 41624,
      "output_tokens": 38008,
      "total_tokens": 79632,
      "cost_usd": 0.060662,
      "impressao": "97c724c12efdaf604f57819549544f78cc28901a9f1ec0686fe1c26ddbc816b5",
      "tests_vermelhos": null
    }
  ],
  "pytest_final": {
    "passed": 0,
    "failed": 0,
    "errors": 0,
    "total": 0
  },
  "integridade": {
    "medido_sha256": "97c724c12efdaf604f57819549544f78cc28901a9f1ec0686fe1c26ddbc816b5",
    "intacto": true
  }
}
```

</details>

<details>
<summary>TDD</summary>

```json
{
  "started_at": "2026-10-18T18:22:29",
  "ended_at": "2026-10-18T19:44:18",
  "total_duration_s": 4908.97,
  "grupo": "tdd",
  "requisito_id": "03-caronte-prejanus-completo",
  "alvo": {
    "comando_app": "uvicorn app:app --host 0.0.0.0 --port {porta}",
    "comando_teste": "pytest -q --tb=short",
    "comando_frontend": "",
    "python": "3.11",
    "pacotes": [
      "pytest==9.0.3",
      "fastapi==0.114.2",
      "uvicorn==0.30.6",
      "sqlalchemy[asyncio]==2.0.43",
      "psycopg[c]==3.2.9",
      "pydantic==2.11.7",
      "pydantic-settings==2.10.1",
      "python-multipart==0.0.17",
      "itsdangerous==2.2.0",
      "httpx==0.27.2",
      "requests==2.32.5",
      "oauthlib==3.3.1",
      "senhaunicapy @ git+https://gitlab.com/ccsl-usp/poscomp-ime/senhaunicapy.git@db099c3532eda31ab6257030ef298290fce59e78",
      "fastapi-mail==1.5.0",
      "email-validator==2.3.0",
      "fpdf2==2.8.4",
      "matplotlib==3.10.7",
      "pypdf==6.1.3",
      "babel==2.17.0",
      "alembic==1.16.5",
      "argon2-cffi==23.1.0"
    ],
    "modelos": {
      "test_writer": "z-ai/glm-5.3",
      "coder": "z-ai/glm-5.3"
    },
    "amostragem": {
      "temperature": 0.1,
      "top_p": 0.9
    }
  },
  "orcamento": {
    "passos": 40,
    "custo_usd": 2.0,
    "tempo_s": 3600
  },
  "total_cost_usd": 0.69564,
  "total_tokens": 969426,
  "total_retries": 8,
  "stages": [
    {
      "id": "tests",
      "configured_model": "z-ai/glm-5.3",
      "duration_s": 83.65,
      "ok": true,
      "motivo": "verde",
      "passos": 1,
      "retries": 0,
      "arquivos": [
        "tests/conftest.py",
        "tests/test_root_auth.py",
        "tests/test_forms.py",
        "tests/test_edicts.py",
        "tests/test_submissions.py",
        "tests/test_evaluation.py",
        "tests/test_selection_reports.py"
      ],
      "historico": [],
      "input_tokens": 41975,
      "output_tokens": 13852,
      "total_tokens": 55827,
      "cost_usd": 0.036938
    },
    {
      "id": "code",
      "configured_model": "z-ai/glm-5.3",
      "duration_s": 4373.91,
      "ok": false,
      "motivo": "tempo",
      "passos": 9,
      "retries": 8,
      "arquivos": [
        "app.py"
      ],
      "historico": [
        {
          "passed": 33,
          "failed": 1,
          "errors": 0,
          "total": 34
        },
        {
          "passed": 0,
          "failed": 30,
          "errors": 5,
          "total": 35
        },
        {
          "passed": 32,
          "failed": 1,
          "errors": 0,
          "total": 33
        },
        {
          "passed": 31,
          "failed": 3,
          "errors": 0,
          "total": 34
        },
        {
          "passed": 0,
          "failed": 30,
          "errors": 5,
          "total": 35
        },
        {
          "passed": 32,
          "failed": 2,
          "errors": 0,
          "total": 34
        },
        {
          "passed": 8,
          "failed": 22,
          "errors": 5,
          "total": 35
        },
        {
          "passed": 0,
          "failed": 30,
          "errors": 5,
          "total": 35
        }
      ],
      "input_tokens": 469285,
      "output_tokens": 444314,
      "total_tokens": 913599,
      "cost_usd": 0.658702,
      "impressao": "9ad8c0d5ea756c235a206769847b1e5d8e41f9237b58bd5aa2c932e35c448689",
      "tests_vermelhos": true
    }
  ],
  "pytest_final": {
    "passed": 0,
    "failed": 30,
    "errors": 5,
    "total": 35
  },
  "integridade": {
    "medido_sha256": "9ad8c0d5ea756c235a206769847b1e5d8e41f9237b58bd5aa2c932e35c448689",
    "intacto": true
  }
}
```

</details>

<details>
<summary>Rework</summary>

```json
{
  "started_at": "2026-10-18T20:16:28",
  "ended_at": "2026-10-18T22:04:33",
  "total_duration_s": 6484.73,
  "grupo": "rework",
  "requisito_id": "entrada-rework",
  "alvo": {
    "comando_app": "uvicorn app:app --host 0.0.0.0 --port {porta}",
    "comando_teste": "pytest -q --tb=short",
    "comando_frontend": "",
    "python": "3.11",
    "pacotes": [
      "pytest==9.0.3",
      "fastapi==0.114.2",
      "uvicorn==0.30.6",
      "sqlalchemy[asyncio]==2.0.43",
      "psycopg[c]==3.2.9",
      "pydantic==2.11.7",
      "pydantic-settings==2.10.1",
      "python-multipart==0.0.17",
      "itsdangerous==2.2.0",
      "httpx==0.27.2",
      "requests==2.32.5",
      "oauthlib==3.3.1",
      "senhaunicapy @ git+https://gitlab.com/ccsl-usp/poscomp-ime/senhaunicapy.git@db099c3532eda31ab6257030ef298290fce59e78",
      "fastapi-mail==1.5.0",
      "email-validator==2.3.0",
      "fpdf2==2.8.4",
      "matplotlib==3.10.7",
      "pypdf==6.1.3",
      "babel==2.17.0",
      "alembic==1.16.5",
      "argon2-cffi==23.1.0"
    ],
    "modelos": {
      "test_writer": "z-ai/glm-5.3",
      "coder": "z-ai/glm-5.3"
    },
    "amostragem": {
      "temperature": 0.1,
      "top_p": 0.9
    }
  },
  "orcamento": {
    "passos": 40,
    "custo_usd": 2.0,
    "tempo_s": 3600
  },
  "total_cost_usd": 0.265139,
  "total_tokens": 295981,
  "total_retries": 1,
  "stages": [
    {
      "id": "code",
      "configured_model": "z-ai/glm-5.3",
      "duration_s": 5132.28,
      "ok": false,
      "motivo": "tempo",
      "passos": 2,
      "retries": 1,
      "arquivos": [
        "app.py"
      ],
      "historico": [
        {
          "passed": 1,
          "failed": 43,
          "errors": 117,
          "total": 161
        },
        {
          "passed": 1,
          "failed": 43,
          "errors": 117,
          "total": 161
        }
      ],
      "input_tokens": 112971,
      "output_tokens": 183010,
      "total_tokens": 295981,
      "cost_usd": 0.265139,
      "impressao": "fa559e66e3941b75d80f7a6edef84589b5e5a7a9c38cbae3cd2c96a165ec64c7",
      "tests_vermelhos": true
    }
  ],
  "pytest_final": {
    "passed": 1,
    "failed": 43,
    "errors": 117,
    "total": 161
  },
  "integridade": {
    "medido_sha256": "fa559e66e3941b75d80f7a6edef84589b5e5a7a9c38cbae3cd2c96a165ec64c7",
    "intacto": true
  }
}
```

</details>
