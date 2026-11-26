---
slug: runs-com-licoes-refeitas
title: "Runs com lições refeitas depois dos consertos no harness"
authors: [eduardo]
tags: [tcc, experimento]
---

Refiz as três condições com gate da [rodada com lições](/blog/runs-com-licoes-prejanus-back):
TDD, rework e TDD com revisão. No gabarito completo, ficaram em 202/247, 216/247 e
217/247; na rodada anterior, em 2/247, 2/247 e 131/247. Os resultados novos
substituem os anteriores no TCC. A baseline não foi refeita. As três runs válidas
custaram US$ 4,17.

<!-- truncate -->

## O que mudou no harness

Antes desta rodada, corrigi os três pontos apontados na rodada anterior:

- uma proposta interrompida por custo ou tempo agora passa pelo gate; fica se
  aprovar pelo menos tantos testes quanto a versão anterior e é revertida se
  aprovar menos (`interrompida` = `mantida` ou `descartada` no `RUN.log`);
- quando o gate falha, o coder recebe os logs da aplicação, além da saída do
  pytest, recortada no começo e no fim até 8000 caracteres;
- no TDD com revisão, a mensagem após um gate vermelho permite corrigir um teste
  errado, com registro em `tests/REVISOES.md`.

Entrada, bloco de lições, modelo (GLM 5.3), gabarito e limites por etapa
(US$ 2, 3600 s, 40 propostas) são os mesmos da rodada anterior.

## Resultados

| Condição | Gabarito completo | Visíveis | Reservados | Custo | Antes (completo / reservados) |
|---|---:|---:|---:|---:|---:|
| Baseline (não refeita) | 138/247 | 86/161 | 51/85 | US$ 0,632258 | — |
| TDD | 202/247 | 137/161 | 64/85 | US$ 1,761775 | 2/247 · 0/85 |
| Rework | 216/247 | 153/161 | 62/85 | US$ 1,109300 | 2/247 · 0/85 |
| TDD com revisão | 217/247 | 144/161 | 72/85 | US$ 1,294074 | 131/247 · 49/85 |

O total de 247 inclui o teste de rastreio dos requisitos, que não entra nem nos
visíveis nem nos reservados. Nenhuma das três entregas teve erro de preparação
no gabarito: todas as falhas são de comportamento.

## Gates do coder

| Condição | Aprovados em cada gate | Encerramento |
|---|---|---|
| TDD | 30, 52, 55, 60 (de 63) | tempo; proposta interrompida aprovou 60/63 e foi mantida |
| Rework | 132, 126, 130, 153 (de 161 visíveis) | tempo; a sessão interrompida não propôs arquivos |
| TDD com revisão | 27, 0, 29, 44, 47, 0, 48, 52, 52, 52, 52, 52, 53 (de 53–55) | verde no passo 13, com 2948 s |

No TDD com revisão, os dois gates com zero foram de aplicações que não iniciaram
(`NameError: SAEnum` e `ImportError` de `NewX` em `fpdf.enums`); nos dois casos,
o coder corrigiu no passo seguinte. Ele registrou quatro revisões de testes, todas
em helpers e fixtures de `tests/test_mail.py` e `tests/conftest.py`.

## Falhas no gabarito por arquivo

| Arquivo | TDD | Rework | TDD com revisão |
|---|---:|---:|---:|
| `test_formularios.py` | 17 | 0 | 0 |
| `test_selecao.py` | 9 | 10 | 9 |
| `test_inscricoes.py` | 7 | 7 | 9 |
| `test_mensagens.py` | 4 | 3 | 3 |
| `test_relatorios.py` | 3 | 4 | 3 |
| `test_avaliacao.py` | 1 | 3 | 3 |
| `test_mapeamentos.py` | 2 | 1 | 1 |
| `test_acesso.py` | 1 | 2 | 1 |
| `test_percursos.py` | 1 | 1 | 1 |
| **Total** | **45** | **31** | **30** |

## Ambiente

O gate rodou no Docker Desktop do WSL. Cada troca dos backends levou cerca de
1,5 a 2 minutos, mais que na rodada anterior; esse tempo conta no teto de 3600 s
da etapa. Uma primeira tentativa do TDD (`…-licoes-tdd-20261125-155604`,
US$ 0,276703) foi abortada porque removi por engano os contêineres do ambiente
durante a run; ela fica preservada e fora dos resultados.

## Artefatos

Em `demos/runs/caronte/`:

- `05-prejanus-back-piloto-v3-licoes-tdd-20261125-162401`
- `05-prejanus-back-piloto-v3-licoes-rework-20261125-174345`
- `05-prejanus-back-piloto-v3-licoes-tdd-revisao-20261125-190444`
