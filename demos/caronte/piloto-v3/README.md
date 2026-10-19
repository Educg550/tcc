# Piloto v3 — baseline modular do PreJanus Back

O v3 repete o escopo das 50 operações do v2 com o harness Agno adaptado para
ferramentas nativas de leitura, criação e substituição de trechos, histórico de
sessão e validação de sintaxe. A separação em módulos é obrigatória no prompt;
`app.py` fica como ponto de entrada. Não há limite artificial de linhas ou arquivos.

A entrada está em `../../requisitos/05-prejanus-back-piloto-v3/`. Contratos SQL,
OpenAPI, dependências, skills, runtime, fixture e oráculo são os mesmos do v2.
Foram removidos avisos de preparação ainda pendente que haviam ficado no rascunho.
O provedor GLM 5.3 fica fixado em `novita/fp8`, sem fallback, como no smoke do
marketplace; a run v2 não havia fixado esse provedor. Isso limita a atribuição
de diferenças exclusivamente à mudança de escrita.

Uma geração baseline, teto US$ 2 e 3600 s. O limite de 40 propostas ao gate é
preservado do v2; chamadas de ferramentas são medidas separadamente. Não há
feedback de testes, correção manual da entrega, CUA ou execução TDD/rework nesta
rodada. O oráculo inteiro é aplicado depois de encerrada a sessão.

De `demos/`, com o ambiente isolado do v2 preparado:

```bash
uv run python -m caronte.piloto_v3
```

A nova pasta em `runs/caronte/05-prejanus-back-piloto-v3-baseline-*` preserva a
entrada, prompts, runtime/provedor, hashes e linhas dos arquivos gerados, métricas
por chamada e resultados do oráculo. O original tem 233/247 casos aprovados;
as 14 divergências conhecidas continuam registradas no protocolo v2.
