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
npm install -g opencode-ai@1.19.0      # o executor das etapas; outra versão é recusada
cp .env.example .env                   # OPENROUTER_API_KEY e as duas ANTHROPIC_*
```

Todos os comandos rodam a partir de `demos/`.

## Um caso de uso

Um requisito é uma pasta em `requisitos/` com três arquivos:

| arquivo | o que é |
|--|--|
| `requisito.md` | o requisito em linguagem natural, entrada dos agentes |
| `criterios.toml` | critérios de aceitação, cada um com `tipo`: `deterministico` vira spec de Cypress, `subjetivo` vai para o CUA (uma sessão por critério) |
| `alvo.toml` | `[comandos]` (app, teste e `teste_frontend`), `[dependencias]` (versão do Python e pacotes), `[modelos]` por etapa, `[orcamento]` e, opcional, `[skills]` com `lock`: o caminho de um manifesto de skills vendorizadas (ex.: `../../caronte/skills.lock.json`) |

Sem `teste_frontend` no `alvo.toml` não há suíte Cypress, e só o CUA avalia - é assim que
um caso de uso sem interface declara que não tem o que medir no navegador.

`requisitos/00-exemplo-caso-de-uso/` é o modelo. Para criar um caso novo a
partir dele, rode `run` sem o segundo argumento. O harness copia o modelo e
abre cada arquivo no `$EDITOR`.

## Executor

Cada etapa é uma sessão do [opencode](https://github.com/anomalyco/opencode) 1.19.0, com o
modelo do `alvo.toml` via OpenRouter. O modelo lê e edita o projeto com as ferramentas que o
escopo da etapa libera: o test writer só escreve em `tests/`, o coder em tudo menos `tests/`,
`pytest.ini`, `conftest.py`, `_harness/` e `.git/`. Bash e as demais ferramentas ficam
negados: quem roda o pytest é o harness, e a falha volta para a mesma sessão. Depois de
cada chamada o harness confere o que mudou em disco; escrita fora do escopo encerra a etapa.

A sessão não enxerga o ambiente de quem roda: `HOME` e XDG próprios, `env` limpo (só `PATH`
e `OPENROUTER_API_KEY`) e as flags de isolamento em `models/sessao.py`. Sem elas o opencode
carrega o `~/.claude/CLAUDE.md`, as skills de `~/.claude` e `~/.agents` e o `AGENTS.md` da
raiz do repositório. `tests/test_sessao.py` roda o opencode contra um provedor falso e
falha se algo disso chegar ao prompt.

Skills: só as do manifesto declarado em `[skills]`, carregadas sob demanda. As de
propósito `testing` só entram na etapa de testes. As usadas ficam em `skills` no `RUN.log`.

O custo de cada etapa é o `cost` que o opencode calcula por passo com a tabela de preços
embutida na versão fixada. O uso da chave no OpenRouter (`GET /api/v1/key`) seria o valor
cobrado, mas chega com minutos de atraso e não separa etapa nem run.

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
Usa DeepSeek V4.1 Flash e GLM-5.3, com os orçamentos dos respectivos `alvo.toml`.
Roda em lotes de até 25 execuções simultâneas, cada uma em sua própria thread;
espera o lote inteiro terminar antes de iniciar o próximo.

Ao executar novamente, pula projetos com `RUN.log`, inclusive os encerrados por
orçamento ou com testes falhando. Uma exceção encerra o batch depois das execuções
do lote atual terminarem. Pastas incompletas são movidas para
`<grupo>-interrompida-<sufixo>/` na mesma pasta-mãe antes de reiniciar do zero,
preservando a tentativa anterior.

## Sintaxe e Radon

```bash
uv run --locked python analisar_batch.py
```

Grava `runs/batch/radon.csv` (duas linhas por run: implementação e testes) e
`runs/batch/radon.json` (métricas por arquivo, hashes e versões de Python/Radon).
Um caminho de batch diferente pode ser passado como argumento.
Analisa as pastas `baseline` e `tdd` de cada `runN`, incluindo runs sem sucesso;
tentativas arquivadas e `_harness`, dependências e pastas ocultas ficam fora.

São testes os arquivos em `tests/` ou `test/`, `conftest.py`, `test_*.py` e
`*_test.py`, inclusive no baseline. Os demais arquivos Python são implementação.
Cada arquivo é compilado em memória antes do Radon, sem executar ou importar o
aplicativo. Sintaxe válida não garante imports, inicialização ou comportamento corretos.
Python ausente e erro de sintaxe ficam explícitos; nesses casos, as métricas
agregadas da parte ficam vazias, e os detalhes dos arquivos válidos permanecem no JSON.

O CSV traz SLOC/LLOC somados, quantidade de funções/métodos (incluindo funções
internas), CC médio/máximo, percentual com CC > 10 e menor MI entre os arquivos.
Classes não são contadas novamente na agregação de CC. O JSON inclui métricas raw,
CC, MI e Halstead; strings multilinha não contam como comentários no MI.
`status=ok` significa apenas sintaxe válida e análise concluída, não correção funcional.
JavaScript, HTML e CSS não são avaliados. Com os mesmos arquivos, Python e lockfile,
as saídas são reproduzíveis: ordem fixa, sem timestamps e sem chamadas a LLMs.

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
- `trace.jsonl` - um evento por chamada à sessão: arquivos alterados, pytest e custo acumulado.
- `opencode/<papel>-<n>.jsonl` - a saída bruta de cada chamada ao opencode.
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
| `models/etapas.py` | o laço de uma etapa: a sessão edita → o harness confere o escopo → observa → autoriza. `Escopo` (onde cada etapa pode escrever), `EtapaTestes`, `EtapaCodigo` (baseline) e `EtapaTDD` (com gate de pytest) |
| `models/propostas.py` | o que sobra da proposta depois de aplicada: `PropostaAceita` ou `PropostaRejeitada` |
| `models/observacoes.py` | o que volta à sessão entre chamadas: `PytestFalhou`, `SessaoFalhou` e o feedback humano |
| `models/sessao.py` | a `Sessao` do opencode: config por etapa, isolamento do ambiente, tokens e custo do JSONL |
| `models/agentes.py` | o `Agente` Agno da avaliação, que traduz resposta de provedor em `Mudanca` (a suíte Cypress) |
| `models/avaliacao.py` | o `Avaliador`: a suíte Cypress sobre os critérios determinísticos e o CUA (browser-use) sobre os subjetivos |
| `models/politicas.py` | `Orcamento` (passos, custo, tempo) e `Permissao` (`Batch`/`Interativa`), que decide por `Aprovado` ou `FeedbackHumano` |
| `models/tracing.py` | classes `Trace`, `Resultado` que viram `RUN.log` |
| `prompts/*.md` | todos os textos de prompt |
