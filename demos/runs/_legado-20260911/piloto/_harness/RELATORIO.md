# Execução piloto — requisito 01, grupo experimental

Primeira execução ponta a ponta do harness final gastando API. Rodada em 2026-08-26,
harness no commit `dd916b7` da branch `feat/harness-oo`, em modo batch (`--yes`), sem
gate humano em nenhuma etapa.

```bash
uv run python -m harness.cli run runs/piloto requisitos/01-formulario-docentes --yes
uv run python -m harness.cli avaliar runs/piloto requisitos/01-formulario-docentes
```

## Resultado

**O pytest passou 10/10 e o CUA reprovou.** O critério C2 falhou:

> O campo 'VALOR SOLICITADO' mostra '1500' em vez de 'R$ 15,00'.

Evidência visual em `C2.png`: o campo com `1500`, o foco já em outro campo, nada
formatado. Conferido no código gerado: `app.py` não tem uma linha de JavaScript, então a
formatação ao digitar simplesmente não existe.

Os testes gerados não tinham como pegar isso. O test-writer usou `TestClient` do FastAPI,
que não executa JavaScript, e cobriu o comportamento adjacente que ele *conseguia*
alcançar: `test_valor_conversion_to_brazilian_currency` envia `1500`, `150000` e
`150000000` por POST e confere `R$ 15,00`, `R$ 1.500,00` e `R$ 1.500.000,00` na resposta.
A conversão no servidor está certa; a formatação na tela, que é o que o requisito pede em
"ao terminar de digitar, deve formatar", não foi implementada nem testada.

É exatamente a hipótese que sustenta o CUA na proposta: divergência semântica que os testes
gerados pelo próprio pipeline não alcançam, detectada por avaliação de caixa-preta.

## Métricas

| Etapa | passos | duração | USD | tokens |
|---|---|---|---|---|
| `tests` (deepseek-v4-flash) | 1 | 26,3 s | 0,000982 | 4.142 |
| `code` (deepseek-v4-flash) | 2 | 422,3 s | 0,001528 | 10.582 |
| **geração (total)** | 3 | 455,1 s | **0,002510** | 14.724 |
| `avaliar` (gemini-2.5-flash, 6 sessões) | 40 | 189,8 s | **0,115350** | 352.866 |

Laço de código: primeira proposta 4/10 passando, segunda 10/10. `tests_vermelhos: true` —
os testes gerados falhavam antes da implementação, não eram tautologia.
`integridade.intacto: true` — os testes medidos no fim são byte-idênticos aos gerados.

| Critério | veredito | passos | duração | USD |
|---|---|---|---|---|
| C1 | passou | 2 | 5,1 s | 0,005019 |
| C2 | **FALHOU** | 6 | 24,4 s | 0,020681 |
| C3 | passou | 4 | 17,2 s | 0,011469 |
| C4 | passou | 9 | 33,7 s | 0,025993 |
| C5 | passou | 10 | 36,7 s | 0,028292 |
| C6 | passou | 9 | 34,7 s | 0,023897 |

## Calibração do orçamento

Os defaults (12 passos / US$ 2 / 900 s por etapa) eram chute. O que esta execução mostra:

- **O teto de custo é inerte.** A geração inteira custou US$ 0,0025, ou 0,13% do teto de
  US$ 2. Nesse modelo ele nunca vai disparar; serve só como rede contra runaway.
- **O teto de tempo é o que morde, e é incoerente com o de passos.** A etapa `code` levou
  422 s em 2 passos, ~210 s por passo. A 900 s, cabem ~4 passos, não 12: o teto de tempo
  corta antes de o de passos ser alcançado. Ou `tempo_s` sobe para ~2.500-3.600 s, ou
  `passos` cai para ~4. Como o número de propostas é a medida de esforço do pipeline, o
  ajuste correto é subir o tempo e deixar os passos mandando.
- **O avaliador custa 46× a geração.** US$ 0,115 contra US$ 0,0025, porque screenshot
  domina o consumo (352 mil tokens em 40 passos). Qualquer estimativa de custo do
  experimento é dominada pelo CUA, não pela geração.
- **Extrapolação.** Por requisito, com os dois grupos: ~US$ 0,235 e ~21 min. Para N=10
  requisitos, ~US$ 2,35 e ~3,5 h de execução.

## Observações sobre o pipeline

1. **Os testes gerados viram a especificação, inclusive na parte inventada.** O
   `requisito.md` pede "placeholders visíveis, claros e autoexplicativos". O test-writer
   assertou `placeholder="NOME COMPLETO - SEM ABREVIAR"`, ou seja, placeholder idêntico ao
   rótulo — um contrato que o requisito não estabelece. O coder obedeceu, e o CUA aprovou o
   C1 assim mesmo. Dado do experimento, não bug: mostra que o agente de testes fecha
   ambiguidade do requisito por conta própria, e que essa decisão passa a valer como
   contrato para o resto do pipeline.
2. **O CUA gastou mais passos nos critérios de validação (C4, C5, C6: 9-10 passos) que no
   caminho felizinho (C3: 4).** Preencher sete campos é a maior parte do custo de cada
   sessão, e os critérios autocontidos pagam isso de novo a cada sessão. É o preço da
   independência entre critérios.

## Nenhum bug de harness nesta execução

Pelo critério do plano, seria bug: `RuntimeError` de app que não sobe, ou traceback fora
disso. Não houve. O que houve antes de rodar, e foi corrigido: o extra `[video]` do
`browser-use` travava a subida do navegador em ~28 s no `LocalBrowserWatchdog`, sem
mensagem. Removido do `pyproject.toml`; o CUA usa o `/usr/bin/google-chrome` do sistema e
não precisa do `playwright install chromium`.

## Arquivos

- `RUN.log` — métricas da geração, com `alvo`, `orcamento` e `integridade`.
- `veredito.json` — veredito do CUA por critério, com passos, duração e custo de cada um.
- `C1.png`..`C6.png` — a última tela que cada sessão viu ao julgar.
- `app-C1.log`..`app-C6.log` — stderr do uvicorn de cada sessão.
- `trace.jsonl` — uma linha por passo de modelo na geração.

O `RUN.log` não contém o bloco `cua`: o `avaliar` é um comando separado e mesclar o
veredito depois do fato deixaria `total_cost_usd` e `total_tokens` do `RUN.log`
inconsistentes com as partes de que são derivados. Os dois arquivos ficam lado a lado e a
análise junta.
