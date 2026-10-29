---
slug: piloto-consulta-caronte
title: "Três runs no piloto de consulta do Caronte"
authors: [eduardo]
tags: [tcc]
---

Terminei as três runs do piloto atual: baseline, TDD e rework. Cada entrega passou em
26 das 27 verificações comportamentais do gabarito, mas as falhas foram diferentes.
O TDD também expôs um desencontro entre os testes gerados e o gate.

<!-- truncate -->

O recorte continua sendo a consulta do prejanus-back: login local, editais, inscrições,
detalhe e oito anexos. Os bancos e os arquivos já vêm preparados. Não reconstruí o forms
nem o frontend, e o CUA ficou fora dessa avaliação.

Usei GLM-5.3 via OpenRouter, com temperatura 0,1 e top-p 0,9. Cada etapa rodou no
OpenCode 1.19.0, em sua imagem oficial fixada por digest. O container só recebeu a pasta
da reconstrução, o estado da sessão e as skills permitidas. O código original e o
gabarito completo ficaram fora dos volumes. As skills foram disponibilizadas sob
demanda; somente o TDD registrou o carregamento de Ponytail.

| Condição | Tempo de geração e gate | Custo registrado (USD) | Gabarito comportamental | Falha |
|---|---:|---:|---:|---|
| Baseline | 70,24 s | 0,059672 | 26/27 | `ethnicity-race` ausente no detalhe |
| TDD | 1.251,15 s | 0,569621 | 26/27 | `ethnicity-race` ausente no detalhe |
| Rework | 112,35 s | 0,033588 | 26/27 | `name` ausente na listagem de inscrições |

O gabarito tem mais uma checagem de rastreio dos requisitos, que passou nos três casos.
Por isso o resumo do pytest mostra 27 aprovados e uma falha em cada entrega.
Login, consulta do edital e os oito downloads passaram nas três reconstruções.

## O gate do TDD

O test-writer escreveu 14 testes com `httpx.Client` apontando para `localhost:8083`,
sem uma fixture que iniciasse a aplicação. O prompt pedia `TestClient`. O gate do TDD
executava pytest em um runtime limpo, com Postgres e uploads, mas não iniciava um
servidor HTTP separado para esses testes.

O coder produziu a aplicação e recebeu as falhas na mesma sessão. Três tentativas
concluídas repetiram o resultado de três falhas e onze erros de conexão. A etapa
terminou pelo limite de 1.200 segundos, com duas chamadas interrompidas. Preservei os
testes e o código gerados; não adaptei o gate durante a run.

Depois, subi a API entregue e apliquei o gabarito externo. Ela passou nas mesmas 26
verificações que o baseline. A falha do gate não impediu que a aplicação fosse
executável, e essa run continua na comparação. Esse resultado identifica uma revisão
necessária no contrato entre test-writer e gate antes de ampliar o experimento.

Há também uma imprecisão no texto da fixture: ele diz que PPI não é verificado, mas
o gabarito confere o valor bruto de `ethnicity-race` no formulário, embora o campo
esteja fora do mapeamento do resumo. Baseline e TDD o retiraram do detalhe. Os
requisitos, a fixture e o gabarito usados nestas runs foram preservados; essa distinção
limita a interpretação da falha.

## O rework e os casos reservados

O rework começou do zero, com os 20 testes visíveis e a infraestrutura declarativa,
sem o código original, as issues ou o código das outras reconstruções. Especializei
as parametrizações visíveis para não entregar junto os sete casos reservados.
Os 20 testes passaram no original antes da execução.

O coder passou nos 20 visíveis na primeira tentativa. Na avaliação externa, passou
em seis dos sete reservados: o caso que exigia o nome do candidato na listagem
encontrou a chave `name` ausente. O detalhe e os anexos passaram. Isso mostra por que
a aprovação no gate visível não pode ser a nota desse experimento.

## Medidas e limites

| Reconstrução | NLOC de implementação | CC médio por função | CC máximo |
|---|---:|---:|---:|
| Baseline | 234 | 2,84 | 9 |
| TDD | 225 | 2,94 | 11 |
| Rework | 164 | 2,80 | 7 |

O lizard 1.24.1 também mediu o original, descontando a lista congelada de código morto.
Esse número abrange o backend inteiro, enquanto as reconstruções cobrem apenas a
consulta; não uso essa diferença de tamanho como evidência de melhoria.

As três runs somaram US$ 0,662881 registrados. Uma tentativa anterior do baseline,
que conseguiu ler arquivos do original, foi invalidada e preservada separadamente;
ela custou US$ 0,086408. O total registrado do piloto ficou em US$ 0,749289, abaixo do
teto de US$ 10. Os custos vêm da tabela do executor; o consumo de chamadas interrompidas
pode não estar integralmente contabilizado nesses valores.

É uma tentativa por condição, num recorte pequeno e fora dos resultados finais.
Nenhuma entrega passou no gabarito inteiro. Guardei os logs, os resultados por rota,
os hashes das entregas e das entradas, a integridade dos testes e as imagens usadas.
O piloto deixou uma falha concreta de integração para resolver antes de aumentar o
escopo; ainda não permite estimar o custo do prejanus-back completo.

## RUN.log das execuções

<details>
<summary>Baseline</summary>

```json
{
  "started_at": "2026-10-17T10:02:05",
  "ended_at": "2026-10-17T10:03:15",
  "total_duration_s": 70.24,
  "grupo": "baseline",
  "requisito_id": "02-caronte-consulta",
  "alvo": {
    "comando_app": "uvicorn app:app --host 0.0.0.0 --port {porta}",
    "comando_teste": "pytest -q --tb=short",
    "comando_frontend": "",
    "python": "3.11",
    "pacotes": [
      "pytest==9.0.3",
      "fastapi==0.114.2",
      "uvicorn==0.30.6",
      "psycopg[binary]==3.2.9",
      "sqlalchemy==2.0.43",
      "pydantic==2.11.7",
      "httpx==0.28.1"
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
    "passos": 1,
    "custo_usd": 2.0,
    "tempo_s": 1200
  },
  "total_cost_usd": 0.059672,
  "total_tokens": 372717,
  "total_retries": 0,
  "stages": [
    {
      "id": "direto",
      "configured_model": "z-ai/glm-5.3",
      "executor": "opencode 1.19.0",
      "imagem": "ghcr.io/anomalyco/opencode@sha256:543fe6b18470c9e4787e9be9813c4d340fba5738085b833ea76fb330ddff514a",
      "sessao": "ses_eb60b52b1ffeMsG7igWkucRWLM",
      "duration_s": 68.95,
      "ok": true,
      "motivo": "verde",
      "passos": 1,
      "retries": 0,
      "arquivos": [
        "app.py"
      ],
      "skills": [],
      "historico": [],
      "input_tokens": 363172,
      "output_tokens": 9545,
      "total_tokens": 372717,
      "cost_usd": 0.059672,
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
  "started_at": "2026-10-17T10:22:42",
  "ended_at": "2026-10-17T10:43:33",
  "total_duration_s": 1251.15,
  "grupo": "tdd",
  "requisito_id": "02-caronte-consulta",
  "alvo": {
    "comando_app": "uvicorn app:app --host 0.0.0.0 --port {porta}",
    "comando_teste": "pytest -q --tb=short",
    "comando_frontend": "",
    "python": "3.11",
    "pacotes": [
      "pytest==9.0.3",
      "fastapi==0.114.2",
      "uvicorn==0.30.6",
      "psycopg[binary]==3.2.9",
      "sqlalchemy==2.0.43",
      "pydantic==2.11.7",
      "httpx==0.28.1"
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
    "passos": 12,
    "custo_usd": 2.0,
    "tempo_s": 1200
  },
  "total_cost_usd": 0.569621,
  "total_tokens": 2006961,
  "total_retries": 4,
  "stages": [
    {
      "id": "tests",
      "configured_model": "z-ai/glm-5.3",
      "executor": "opencode 1.19.0",
      "imagem": "ghcr.io/anomalyco/opencode@sha256:543fe6b18470c9e4787e9be9813c4d340fba5738085b833ea76fb330ddff514a",
      "sessao": "ses_eb5f874faffek00bSh3vjCaDPd",
      "duration_s": 44.32,
      "ok": true,
      "motivo": "verde",
      "passos": 1,
      "retries": 0,
      "arquivos": [
        "tests/test_consulta.py"
      ],
      "skills": [],
      "historico": [],
      "input_tokens": 183551,
      "output_tokens": 3316,
      "total_tokens": 186867,
      "cost_usd": 0.022978
    },
    {
      "id": "code",
      "configured_model": "z-ai/glm-5.3",
      "executor": "opencode 1.19.0",
      "imagem": "ghcr.io/anomalyco/opencode@sha256:543fe6b18470c9e4787e9be9813c4d340fba5738085b833ea76fb330ddff514a",
      "sessao": "ses_eb5f795d7ffe1X45AeKMBGoLk6",
      "duration_s": 1201.38,
      "ok": false,
      "motivo": "tempo",
      "passos": 5,
      "retries": 4,
      "arquivos": [
        "app.py"
      ],
      "skills": [
        "ponytail"
      ],
      "historico": [
        {
          "passed": 0,
          "failed": 3,
          "errors": 11,
          "total": 14
        },
        {
          "passed": 0,
          "failed": 3,
          "errors": 11,
          "total": 14
        },
        {
          "passed": 0,
          "failed": 3,
          "errors": 11,
          "total": 14
        }
      ],
      "input_tokens": 1719842,
      "output_tokens": 100252,
      "total_tokens": 1820094,
      "cost_usd": 0.546643,
      "impressao": "ab38274a8678765d6d5950e74517e0431381145d6e563e9dc3a0a7599f0422e4",
      "tests_vermelhos": true
    }
  ],
  "pytest_final": {
    "passed": 0,
    "failed": 3,
    "errors": 11,
    "total": 14
  },
  "integridade": {
    "medido_sha256": "ab38274a8678765d6d5950e74517e0431381145d6e563e9dc3a0a7599f0422e4",
    "intacto": true
  }
}
```

</details>

<details>
<summary>Rework</summary>

```json
{
  "started_at": "2026-10-17T10:44:19",
  "ended_at": "2026-10-17T10:46:11",
  "total_duration_s": 112.35,
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
      "psycopg[binary]==3.2.9",
      "sqlalchemy==2.0.43",
      "pydantic==2.11.7",
      "httpx==0.28.1"
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
    "passos": 12,
    "custo_usd": 2.0,
    "tempo_s": 1200
  },
  "total_cost_usd": 0.033588,
  "total_tokens": 219693,
  "total_retries": 0,
  "stages": [
    {
      "id": "code",
      "configured_model": "z-ai/glm-5.3",
      "executor": "opencode 1.19.0",
      "imagem": "ghcr.io/anomalyco/opencode@sha256:543fe6b18470c9e4787e9be9813c4d340fba5738085b833ea76fb330ddff514a",
      "sessao": "ses_eb5e3f6f2ffet536NIdfXaI4In",
      "duration_s": 101.15,
      "ok": true,
      "motivo": "verde",
      "passos": 1,
      "retries": 0,
      "arquivos": [
        "app.py"
      ],
      "skills": [],
      "historico": [
        {
          "passed": 20,
          "failed": 0,
          "errors": 0,
          "total": 20
        }
      ],
      "input_tokens": 214405,
      "output_tokens": 5288,
      "total_tokens": 219693,
      "cost_usd": 0.033588,
      "impressao": "c7854bc7f939b534402cb594a37db4492258da71f00fb92d4585a124812f708e",
      "tests_vermelhos": true
    }
  ],
  "pytest_final": {
    "passed": 20,
    "failed": 0,
    "errors": 0,
    "total": 20
  },
  "integridade": {
    "medido_sha256": "c7854bc7f939b534402cb594a37db4492258da71f00fb92d4585a124812f708e",
    "intacto": true
  }
}
```

</details>

