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

Um requisito é uma pasta em `requisitos/` com quatro arquivos:

| arquivo | o que é |
|--|--|
| `requisito.md` | o requisito em linguagem natural, entrada dos agentes |
| `criterios.toml` | critérios de aceitação que o CUA vai conferir na tela (um por sessão) |
| `alvo.toml` | como rodar o alvo: `comando_app`, `comando_teste`, modelos por etapa e orçamento |
| `requirements.txt` | dependências do projeto gerado, isoladas do venv do harness |

`requisitos/00-exemplo-caso-de-uso/` é o modelo. Para criar um caso novo a
partir dele, rode `run` sem o segundo argumento. O harness copia o modelo e
abre cada arquivo no `$EDITOR`.

## Os dois modos

Não existe flag de modo. Quem decide é o estado do diretório do projeto:

```bash
uv run python -m harness.cli run <projeto> <requisito>
```

**Do zero (`criacao`)** - `<projeto>` não existe ou está vazio. O modelo não
recebe contexto de código e não há baseline de testes.

```bash
uv run python -m harness.cli run runs/financeiro requisitos/01-formulario-docentes
```

**Edição (`manutencao`)** - `<projeto>` já tem arquivos. O harness roda o
`pytest` antes de tudo para gravar o baseline (`antes` no `RUN.log`, usado para
detectar regressão) e injeta o código atual no prompt como `## PROJETO ATUAL`.
É o mesmo comando, apontando para um projeto que já existe:

```bash
uv run python -m harness.cli run runs/financeiro requisitos/02-listagem
```

Em ambos os modos, cada requisito vira um commit no repositório do projeto
gerado.

### Flags

- `--yes` - modo batch, sem gate humano. É o modo do experimento: os dois grupos recebem a mesma ajuda humana, nenhuma. Sem a flag a execução é interativa e pausa em cada etapa pedindo `y/n`, exigindo feedback textual no `n`.
- `--direto` - grupo baseline: uma etapa só, requisito → código, sem testes gerados nem CI. A ausência das etapas é a variável independente do experimento.

## Reavaliar

Re-roda só o CUA sobre a última run e regrava o campo `cua` do `RUN.log`
existente - não abre run nova, porque o veredito pertence à execução que gerou
o código.

```bash
uv run python -m harness.cli avaliar runs/financeiro requisitos/01-formulario-docentes
```

## Saída

Uma pasta por execução em `<projeto>/_harness/<timestamp>-<requisito>/`:

- `RUN.log` - a medida do TCC: duração, tokens, custo USD e retries por etapa, `pytest_final`, `regressao`, `integridade` dos testes e o veredito do CUA.
- `trace.jsonl` - um evento por ação proposta pelo modelo.
- `veredito.json` - saída estruturada do CUA.
- `<criterio>.png` e `app-<criterio>.log` - tela final e log do app em cada sessão do CUA.

O diretório `_harness/` fica fora do contexto enviado ao modelo: é a medição, e
não pode vazar para dentro do que ela mede.

## Pacote

| | |
|--|--|
| `cli.py` | os dois comandos, `run` e `avaliar` |
| `models/dominio.py` | tudo que o modelo vê e interage com: `Requisito`, `Alvo`, `Projeto`, `Escopo`, `Modo` |
| `models/harness.py` | o loop: `HarnessTDD` (experimental) e `HarnessDireto` (baseline) |
| `models/etapas.py` | o laço de uma etapa: propor → validar → escrever → observar → autorizar |
| `models/agentes.py` | os agentes Agno e o `Avaliador` (CUA via browser-use) |
| `models/politicas.py` | `Orcamento` (passos, custo, tempo) e `Permissao` (`Batch`/`Interativa`) |
| `models/tracing.py` | classes `Trace`, `Resultado` que viram `RUN.log` |
| `prompts/*.md` | todos os textos de prompt |
