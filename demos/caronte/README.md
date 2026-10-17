# Piloto de consulta

Baseline, TDD e rework deste recorte foram concluídos em 17/10/2026;
os resultados estão em `../runs/caronte/RESUMO.json`. A ampliação para o
backend completo está separada em [`piloto-v2/`](./piloto-v2/README.md).

Recorte congelado do prejanus-back: login local, editais, inscrições, detalhe
e anexos. Requisitos e oráculo estão em `requisitos.md` e `oraculo/`.

O baseline está preservado em
`../runs/caronte/02-caronte-consulta-baseline-20261017-100205/`.
Para gerar novas entregas TDD e rework desse mesmo recorte, a partir de
`demos/`:

```bash
uv run python -m caronte.piloto tdd
uv run python -m caronte.piloto rework
```

Esses comandos usam os bancos privados `caronte_{forms,prejanus}_{tdd,rework}_20261017`,
preparados com os esquemas do original e as mesmas fixtures SQL deste diretório.
O runtime limpo é a imagem congelada em `piloto.RUNTIME`, construída com o
Dockerfile e as dependências transitivas guardados no `_harness/runtime/` do
baseline. O OpenCode usa a imagem oficial fixada em `harness/models/sessao.py`.

No TDD, test-writer e coder usam sessões distintas. Para novas execuções,
os dois grupos recebem no gate as URLs `CARONTE_API` e
`CARONTE_API_SEM_ATALHO`, com e sem atalho de autenticação. O pytest roda
com dependências declaradas, Postgres e uploads em container. Essa correção
não altera os resultados nem os snapshots do TDD medido no v1. No rework,
os 20 casos visíveis são fornecidos antes do coder. A exportação especializa os parâmetros
visíveis, sem copiar os casos reservados. `entrada-rework/` contém essa entrada.

As etapas têm US$ 2, 12 passos e 1200 segundos. O custo é verificado após
cada sessão, não é um limite de cobrança por requisição. A soma das chamadas
medidas do piloto tem teto de US$ 10. Os dois comandos geram novas pastas e
não corrigem nem reutilizam a entrega do baseline.

`piloto.avaliar` aplica o oráculo inteiro somente depois da geração e grava
`ORACULO.json`, JUnit e logs. No rework, a nota principal são os 7 reservados;
o resultado nos visíveis é diagnóstico. Restaurar a fixture privada antes
dessa avaliação. O CUA fica fora deste recorte.
