# harness

Orquestrador final do TCC: recebe um requisito, escreve código até o `pytest`
passar e fecha com a avaliação do comportamento sobre o app rodando.

A avaliação tem dois instrumentos. Uma suíte Cypress, escrita a partir dos critérios
determinísticos, julga o que se verifica sem julgamento - texto na tela, valor de campo,
mensagem - e dá veredito repetível em segundos. O CUA julga o que sobra: identidade
visual, proporção, o que só se decide olhando. Os dois rodam depois do código e são
idênticos nos dois grupos, então a régua não muda entre baseline e experimental.

## Preparar

```bash
uv sync
uv run playwright install chromium     # o CUA usa Playwright
npm install                            # o Cypress da avaliação, um install para todas as runs
cp .env.example .env                   # OPENROUTER_API_KEY e as duas ANTHROPIC_*
```

Todos os comandos rodam a partir de `demos/`.

## Um caso de uso

Um requisito é uma pasta em `requisitos/` com três arquivos:

| arquivo | o que é |
|--|--|
| `requisito.md` | o requisito em linguagem natural, entrada dos agentes |
| `criterios.toml` | critérios de aceitação, cada um com `tipo`: `deterministico` vira spec de Cypress, `subjetivo` vai para o CUA (uma sessão por critério) |
| `alvo.toml` | `[comandos]` (app, teste e `teste_frontend`), `[dependencias]` (versão do Python e pacotes), `[modelos]` por etapa e `[orcamento]` |

Sem `teste_frontend` no `alvo.toml` não há suíte Cypress, e só o CUA avalia - é assim que
um caso de uso sem interface declara que não tem o que medir no navegador.

`requisitos/00-exemplo-caso-de-uso/` é o modelo. Para criar um caso novo a
partir dele, rode `run` sem o segundo argumento. O harness copia o modelo e
abre cada arquivo no `$EDITOR`.

## Rodar

```bash
uv run python -m harness.cli run <destino> <requisito>
```

`<destino>` é só a pasta-mãe. Quem nomeia o projeto é o harness, como
`<requisito>-<grupo>-<data>`: toda run parte de um diretório novo, porque reaproveitar o
de uma run anterior mediria manutenção de código que já existe, e não a geração que o
experimento compara.

```bash
uv run python -m harness.cli run runs requisitos/01-formulario-docentes
# → runs/01-formulario-docentes-tdd-20260911-112234/
```

### Flags

- `--yes` - modo batch, sem gate humano. É o modo do experimento: os dois grupos recebem a mesma ajuda humana, nenhuma. Sem a flag a execução é interativa e pausa em cada etapa pedindo `y/n`, exigindo feedback textual no `n`.
- `--direto` - grupo baseline: uma etapa só, requisito → código, sem testes gerados nem CI. A ausência das etapas é a variável independente do experimento.

## Batch por provider

```bash
uv run python -m harness.batch
```

Executa 50 pares TDD/baseline para cada requisito
`01-formulario-docentes-{deepseek,glm}`, sem gate humano e sem
avaliação (CUA ou Cypress). São 200 execuções em 100 pastas-mãe:
`runs/batch/<deepseek|glm>/run<1..50>/<tdd|baseline>/`, com as métricas em `_harness/RUN.log`.
Usa os modelos e orçamentos dos respectivos `alvo.toml`.
Roda em lotes de até 25 execuções simultâneas, cada uma em sua própria thread;
espera o lote inteiro terminar antes de iniciar o próximo.

Ao executar novamente, pula projetos com `RUN.log`, inclusive os encerrados por
orçamento ou com testes falhando. Uma exceção encerra o batch depois das execuções
do lote atual terminarem. Pastas incompletas são movidas para
`<grupo>-interrompida-<sufixo>/` na mesma pasta-mãe antes de reiniciar do zero,
preservando a tentativa anterior.

## Reavaliar

Re-roda só a avaliação sobre um projeto já gerado e regrava o `AVALIACAO.log` dele - não
abre projeto novo, porque o veredito pertence à execução que gerou o código. A suíte
Cypress anterior é descartada e reescrita, para que specs velhos não rodem junto.

```bash
uv run python -m harness.cli avaliar runs/01-formulario-docentes-tdd-20260911-112234 requisitos/01-formulario-docentes
```

## Saída

Uma pasta por projeto gerado, em `<destino>/<requisito>-<grupo>-<data>/_harness/`, onde
`<grupo>` é `tdd` ou `baseline`:

- `RUN.log` - a medida do pipeline: duração, tokens, custo USD e retries por etapa, `pytest_final` e `integridade` dos testes.
- `AVALIACAO.log` - a medida do comportamento: veredito por critério, dos dois instrumentos, com o custo de cada um. Fica fora do `RUN.log` porque mede o app rodando, não o pipeline que o escreveu.
- `trace.jsonl` - um evento por ação proposta pelo modelo.
- `cypress/e2e/*.cy.js` - a suíte gerada, e `cypress.config.js`. Ficam aqui, e não na raiz do projeto, porque são medição: o coder não pode escrever em `_harness/`.
- `<criterio>.png` e `app-<criterio>.log` - tela final e log do app em cada sessão do CUA.

O diretório `_harness/` fica fora do contexto enviado ao modelo: é a medição, e
não pode vazar para dentro do que ela mede.

## Pacote

| | |
|--|--|
| `cli.py` | os dois comandos, `run` e `avaliar` |
| `models/dominio.py` | tudo que o modelo vê e interage com: `Requisito` (o caso de uso em disco), `Alvo` (como rodar o gerado), `Projeto` |
| `models/harness.py` | o loop: `HarnessTDD` (experimental) e `HarnessDireto` (baseline) |
| `models/etapas.py` | o laço de uma etapa: propor → validar → escrever → observar → autorizar. `Escopo` (onde cada etapa pode escrever), `EtapaTestes`, `EtapaCodigo` (baseline) e `EtapaTDD` (com gate de pytest) |
| `models/propostas.py` | o que sobra da proposta depois de aplicada: `PropostaAceita` ou `PropostaRejeitada` |
| `models/observacoes.py` | o que volta ao modelo entre propostas: `PytestFalhou`, e as rejeições |
| `models/agentes.py` | os agentes Agno: `Agente`, que traduz resposta de provedor em `Mudanca` |
| `models/avaliacao.py` | o `Avaliador`: a suíte Cypress sobre os critérios determinísticos e o CUA (browser-use) sobre os subjetivos |
| `models/politicas.py` | `Orcamento` (passos, custo, tempo) e `Permissao` (`Batch`/`Interativa`), que decide por `Aprovado` ou `FeedbackHumano` |
| `models/tracing.py` | classes `Trace`, `Resultado` que viram `RUN.log` |
| `prompts/*.md` | todos os textos de prompt |
