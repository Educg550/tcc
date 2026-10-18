# Piloto v2 — backend completo do PreJanus

Rascunho de escopo preparado em 17/10/2026. O piloto v1 de consulta foi
concluído com baseline, TDD e rework; seus requisitos, oráculo, fixtures,
logs e resultados ficam preservados. O v2 amplia a reconstrução para
todo o `prejanus-back` e suas integrações. Não há execução paga v2.

A entrada de reconstrução está em
[`../../requisitos/03-caronte-prejanus-completo/requisito.md`](../../requisitos/03-caronte-prejanus-completo/requisito.md).
O OpenAPI original acompanha essa entrada como contrato declarativo.
[`interfaces.json`](./interfaces.json) relaciona cada uma das 50 operações
com seu requisito, fonte e integrações. [`avaliacao.md`](./avaliacao.md)
descreve os estados e evidências necessários para avaliar o novo escopo.

| Dimensão | Piloto v1 | Piloto v2 |
|---|---|---|
| Produto reconstruído | Consulta do PreJanus Back | Todas as 50 operações do backend |
| Formulários | Candidatura de mestrado preparada | Mestrado, doutorado, recomendação e aceite; versões distintas |
| Banco Forms | Leitura | Leitura e escrita pelas integrações |
| Identidade | Atalho local e 401 sem sessão | Também OAuth, whitelist e sessão com provedor local |
| Comunicação | Fora do recorte | Solicitação de correção, convite de aceite e carta no SMTP local |
| Relatórios | Fora do recorte | Participantes, PDF e matriz de interesses em CSV |
| Estado | Consulta pré-carregada | Também criação, alterações, fases e percursos completos |
| Clientes e dependências | Bancos e uploads | Também Forms, Front, proxy e serviços auxiliares originais |

Os três grupos continuam: geração agêntica direta (baseline), TDD e rework
a partir dos testes visíveis. A infraestrutura comum é OpenCode 1.19.0 na
imagem fixada, GLM 5.3 via OpenRouter, temperatura 0.1, top-p 0.9 e o mesmo
inventário de skills de implementação. Não juntar as amostras v1 e v2.
A nova ampliação não autoriza automaticamente outras chamadas pagas.

Ambiente, fixture e suíte-oráculo estão materializados: `ambiente.py
preparar` sobe o projeto Compose isolado e grava `dados/`; `oraculo/` roda
contra o original pelo proxy HTTPS (de `demos/`: `uv run pytest
caronte/piloto-v2/oraculo -p no:cacheprovider`). No original, falham só os
casos registrados em `oraculo/divergencias.json`. Decisões e split
75/25 (`oraculo/split.json`) estão registrados em `avaliacao.md`. O
problema do gate TDD registrado em `tcc-hqt.12` precisa ser resolvido antes
de executar o novo grupo.
## Execução

De `demos/`, com o ambiente de pé (`uv run python caronte/piloto-v2/ambiente.py preparar`):

```bash
uv run python -m caronte.piloto_v2 baseline|tdd|rework
uv run python -m caronte.piloto_v2 avaliar ../runs/caronte/<run>
```

O candidato substitui os três backends do Compose (`prejanus-back`, `local`,
`sem-atalho`) por um override; proxy, Forms, OAuth e SMTP continuam os
originais. O runtime (`runtime/Dockerfile`) é a imagem do original sem `src/`
e com pytest: mesmas dependências exatas, listadas no `alvo.toml`. No gate do
TDD, os testes do agente rodam num container desse runtime com
`CARONTE_API=http://local:8000` e `CARONTE_API_SEM_ATALHO`. No rework, o gate
executa a cópia do avaliador das 94 funções visíveis, não a do workspace;
`entrada-rework/` é gerada a partir do split. Ensaiado sem modelo em
17/10/2026: o original como candidato dá 233/247 na avaliação, igual à imagem
original; o gate TDD aprova testes válidos e reprova entrega sem `app.py`
(`tests/test_gate_piloto_v2.py`); o gate do rework reprova só nas 8
divergências visíveis.

Tentativas inválidas do baseline, preservadas em `../../runs/caronte/` e
fora dos resultados: `…-20261017-133643` (US$ 0,16) terminou sem código porque o
opencode cortava a saída do GLM 5.3 em 32k tokens, todos gastos em raciocínio;
`…-20261018-132235` (US$ 0,51, 33/247) recebeu uma entrada sem os esquemas SQL e
sem o contrato de dados do usuário da Senha Única, e o login de todos os perfis
falhou. As duas lacunas eram do pacote, não do modelo: os limites do modelo
estão declarados em `harness/models/sessao.py`, os esquemas e o contrato OAuth
em `infra/`, e o ambiente apaga tabelas criadas por um candidato antes do
próximo.

Orçamento por etapa: US$ 2, 40 passos, 3600 s. No pior caso as quatro
etapas (baseline, test-writer e coder do TDD, rework) somam US$ 8, dentro do
saldo de US$ 9,25 do teto de US$ 10 do piloto.

Tarefas e dependências são mantidas no beads; estes documentos são o
contrato e o protocolo, não uma lista de tarefas.
