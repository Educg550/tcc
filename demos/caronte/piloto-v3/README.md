# Piloto v3 — baseline modular do PreJanus Back

O v3 repete o escopo das 50 operações do v2 com o harness Agno adaptado para
ferramentas nativas de leitura, criação e substituição de trechos, histórico de
sessão e validação de sintaxe. A separação em módulos é obrigatória no prompt;
`app.py` fica como ponto de entrada. Não há limite artificial de linhas ou arquivos.

A entrada está em `../../requisitos/05-prejanus-back-piloto-v3/`. Contratos SQL,
OpenAPI, dependências, skills, runtime, fixture e gabarito são os mesmos do v2.
Foram removidos avisos de preparação ainda pendente que haviam ficado no rascunho.
O provedor GLM 5.3 fica fixado em `novita/fp8`, sem fallback, como no smoke do
marketplace; a run v2 não havia fixado esse provedor. Isso limita a atribuição
de diferenças exclusivamente à mudança de escrita.

Uma geração baseline, teto US$ 2 e 3600 s. O limite de 40 propostas ao gate é
preservado do v2; chamadas de ferramentas são medidas separadamente. Não há
feedback de testes, correção manual da entrega, CUA ou execução TDD/rework nesta
rodada. O gabarito inteiro é aplicado depois de encerrada a sessão.

De `demos/`, com o ambiente isolado do v2 preparado:

```bash
uv run python -m caronte.piloto_v3
```

A nova pasta em `runs/caronte/05-prejanus-back-piloto-v3-baseline-*` preserva a
entrada, prompts, runtime/provedor, hashes e linhas dos arquivos gerados, métricas
por chamada e resultados do gabarito. O original tem 233/247 casos aprovados;
as 14 divergências conhecidas continuam registradas no protocolo v2.

## Execução de 19/10/2026

Run `05-prejanus-back-piloto-v3-baseline-20261019-095708`: 17 arquivos Python,
2.865 linhas, `app.py` com 39 linhas, 24 chamadas em uma sessão. Custo US$ 0,379988
de US$ 2; geração em 550,01 s; pico de entrada 93.334 tokens (8,90% da janela).
A API iniciou e declarou as 50 operações, mais duas extras.

Gabarito: 26/247 aprovados, 69 falhas e 152 erros de preparação por OAuth.
Um aprovado é a rastreabilidade da suíte: são 25/246 casos comportamentais.
Visíveis: 15/161; reservados: 10/85. O código concatena host e recurso sem a barra
necessária, produzindo `http://oauth:8000wsusuario/...` e login 500. A entrega não
foi corrigida. Não houve nova geração, TDD/rework ou CUA. A referência 233/247 do
original é histórica; uma conferência adicional foi interrompida após 26 aprovados.

Entrega, entrada, prompts, manifesto, métricas e gabarito ficam em `../../runs/caronte/`
na pasta da run. O diário detalha o resultado em
`../../../blog/2026-10-19-piloto-v3-baseline-modular.md`.
