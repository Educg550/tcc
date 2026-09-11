# harness

Orquestrador final do TCC: recebe um requisito, escreve código até o `pytest`
passar e fecha com o CUA validando o comportamento na tela.

## Preparar

```bash
uv sync
uv run playwright install chromium     # o CUA usa Playwright
cp .env.example .env                   # OPENROUTER_API_KEY e as duas ANTHROPIC_*
```

Todos os comandos rodam a partir de `demos/`.

## Um caso de uso

Um requisito é uma pasta em `requisitos/` com três arquivos:

| arquivo | o que é |
|--|--|
| `requisito.md` | o requisito em linguagem natural, entrada dos agentes |
| `criterios.toml` | critérios de aceitação que o CUA vai conferir na tela (um por sessão) |
| `alvo.toml` | `[comandos]` (app e teste), `[dependencias]` (versão do Python e pacotes), `[modelos]` por etapa e `[orcamento]` |

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

## Reavaliar

Re-roda só o CUA sobre um projeto já gerado e regrava o `CUA.log` dele - não abre projeto
novo, porque o veredito pertence à execução que gerou o código.

```bash
uv run python -m harness.cli avaliar runs/01-formulario-docentes-tdd-20260911-112234 requisitos/01-formulario-docentes
```

## Saída

Uma pasta por projeto gerado, em `<destino>/<requisito>-<grupo>-<data>/_harness/`, onde
`<grupo>` é `tdd` ou `baseline`:

- `RUN.log` - a medida do pipeline: duração, tokens, custo USD e retries por etapa, `pytest_final` e `integridade` dos testes.
- `CUA.log` - a medida do comportamento: veredito por critério de aceitação, com custo e passos do CUA. Fica fora do `RUN.log` porque mede o app rodando, não o pipeline que o escreveu.
- `trace.jsonl` - um evento por ação proposta pelo modelo.
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
| `models/agentes.py` | os agentes Agno e o `Avaliador` (CUA via browser-use) |
| `models/politicas.py` | `Orcamento` (passos, custo, tempo) e `Permissao` (`Batch`/`Interativa`), que decide por `Aprovado` ou `FeedbackHumano` |
| `models/tracing.py` | classes `Trace`, `Resultado` que viram `RUN.log` |
| `prompts/*.md` | todos os textos de prompt |
