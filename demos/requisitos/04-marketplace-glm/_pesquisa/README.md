# Smoke de escala do harness

Uma geração baseline com GLM 5.3 e teto total de US$ 3, antes de repetir o piloto
Caronte. A aplicação tem 12 blocos funcionais, frontend e backend na stack do
PreJanus. O requisito inteiro entra na sessão; não há compactação, fragmentação em
sessões nem feedback de execução ao modelo.

De `demos/`: `AGNO_TELEMETRY=false uv run --locked python -m marketplace`.
Cada execução cria uma pasta nova em `runs/marketplace/`. Não há repetição automática.

O runner fixa `novita/fp8`, sem fallback, e aceita no máximo US$ 0,70 por milhão de
tokens de entrada e US$ 2,20 por milhão de saída, conforme o snapshot público
`glm-5.3-endpoints.json`. A janela desse endpoint é 1.048.576 tokens. As chamadas
mantêm o teto de saída de 100.000 tokens e o de raciocínio de 32.000 do harness.

Antes de cada chamada, reserva-se a saída máxima e um limite conservador da entrada
calculado pelos bytes da requisição, com folga de formatação. A reserva não é gasto;
serve para recusar uma chamada que poderia ultrapassar o saldo. Se o provedor não
informar custo, a sessão termina para impedir novas chamadas sem contabilidade.

`_harness/chamadas_modelo.jsonl` registra início, fim ou erro de cada chamada, tamanho
da requisição, número de mensagens, sessão, provedor, ID da resposta, ferramentas,
tokens e custo. `contexto_max_tokens` no RUN.log é o maior input informado pelo
provedor, incluindo cache; o total acumulado de tokens não representa a ocupação da
janela. Somar input e output de cada chamada permite medir também o pico do contexto
durante a resposta. Erros de contexto ficam no mesmo JSONL.

A geração não recebe testes prontos nem feedback do build. O pytest final pode
registrar zero testes, porque o grupo é baseline. A verificação posterior deve
registrar separadamente build do frontend, inicialização com PostgreSQL e fluxos
HTTP/navegador, sem corrigir manualmente a entrega. Não há avaliação CUA nesta rodada.

Fontes: [endpoint do modelo](https://openrouter.ai/api/v1/models/z-ai/glm-5.3/endpoints)
e [limite de preços](https://openrouter.ai/docs/guides/routing/provider-selection#max-price).
