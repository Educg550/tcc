# Análise estática do PreJanus-back

Coleta de 29/10/2026, com lizard 1.24.1 e Radon 6.0.1. Inclui as três
entregas principais válidas de 23–24/10 e a variante exploratória de 27/10.

Reprodução, a partir de `demos/`:

```bash
uv run python -m caronte.analisar_estatica
uv run pytest tests/test_analisar_estatica.py -q
uv run python -m caronte.analisar_testes
uv run pytest tests/test_analisar_testes.py -q
```

`estatica.json` guarda as métricas por arquivo e função, os hashes das fontes,
do manifesto de cada run, do coletor e da lista de exclusões. `estatica.csv`
contém o resumo sem arredondamento. O coletor não importa nem executa as
aplicações. Os relatórios são determinísticos e ficam fora das pastas das runs.

## Testes e gabarito

`testes.json` conserva as métricas de Lizard e Radon por arquivo e função,
com hashes; `testes.csv` resume o Lizard, usado na tabela do diário.
O coletor `caronte/analisar_testes.py` reutiliza a análise do coletor de produção.
Seleciona apenas arquivos Python de tipo `testes_autorais` ou `testes_fornecidos`
nos manifestos das mesmas quatro runs, conferindo seus hashes. São os testes
finais, incluindo revisões, fixtures e auxiliares; a baseline não tem testes
próprios. A contagem de funções inclui auxiliares e não equivale a casos pytest.

O gabarito completo é medido separadamente: `test_*.py` e `conftest.py` de
`demos/caronte/piloto-v2/gabarito/`, mais `ambiente.py` do diretório pai,
usado pelas fixtures. `split.py`, que gera a partição, não faz parte da suíte
medida. Os testes visíveis do rework são um subconjunto do gabarito com suporte
adaptado; essas linhas não são independentes nem devem ser somadas.
Nenhum teste ou serviço da aplicação é executado para coletar essas métricas.

## Seleção e exclusões

- Original: cópia em `caronte-core/prejanus-back`, identificada na pesquisa
  pelo commit upstream `46b89c1d5519aeae40c088ee94262e9b739a7d48`.
  Os 84 hashes SHA-256 conferem com os registrados na seção `original` de
  `demos/runs/caronte/02-caronte-consulta-baseline-20261017-100205/_harness/LIZARD.json`.
  O commit upstream não está disponível no histórico Git local; a conferência
  usa os hashes individuais da coleta histórica.
- Excluídos testes, conftest, migrações, diretórios ocultos e caches do original.
  A contagem não inclui todos os arquivos Python mencionados em inventários
  anteriores, que podiam incluir testes.
- `original_vivo`: dez faixas de `demos/caronte/codigo-morto.json` substituídas
  por linhas vazias em memória, preservando a numeração. São as mesmas exclusões
  congeladas usadas na análise anterior. A lista é uma aproximação estática;
  não significa que todo código restante tenha sido exercitado.
- Entregas: apenas arquivos Python de tipo `producao` no manifesto de entrega.
  Cada hash é conferido antes da análise. Testes autorais/fornecidos,
  infraestrutura semeada e arquivos do harness ficam fora.
- Não se aplicam posições de linha do original às reconstruções, nem se roda
  uma nova seleção de código morto nos gerados. Mede-se toda a produção entregue.

## Lizard

NLOC é a contagem de linhas de código do lizard. CC é complexidade ciclomática.
As médias de CC e NLOC por função dão o mesmo peso a cada função/método detectado.
`CC > 10` é uma contagem descritiva, sem excluir funções da análise.

| Entrega | Arquivos | NLOC | Funções | CC média | CC máxima | CC > 10 | NLOC/função média | NLOC/função máxima |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original bruto | 84 | 4847 | 157 | 3,81 | 84 | 8 | 20,54 | 243 |
| Original sem faixas mortas | 84 | 4723 | 153 | 3,81 | 84 | 8 | 20,42 | 243 |
| Baseline | 17 | 1730 | 126 | 3,46 | 22 | 6 | 11,58 | 52 |
| TDD | 17 | 2563 | 139 | 3,80 | 26 | 11 | 14,96 | 59 |
| Rework | 17 | 2110 | 146 | 3,06 | 19 | 6 | 11,40 | 55 |
| TDD com revisão (exploratório) | 17 | 2059 | 121 | 3,95 | 29 | 8 | 14,97 | 62 |

## Radon

SLOC conta linhas físicas de código; LLOC conta instruções lógicas. As médias
de CC incluem funções, métodos e funções internas, sem somar os blocos de
classe como funções adicionais. As regras de contagem diferem das do lizard;
os valores das ferramentas não devem ser fundidos em uma única série.

O índice de manutenibilidade (MI) é calculado por arquivo, com `multi=False`.
A tabela apresenta mediana e mínimo entre arquivos com SLOC maior que zero;
arquivos vazios ficam fora dessa agregação. Não há um MI global do projeto.
O JSON também conserva as métricas brutas e Halstead por arquivo, sem
transformar estimativas Halstead de defeitos em bugs observados.

| Entrega | SLOC | LLOC | CC média | CC máxima | CC > 10 | MI mediano | MI mínimo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original bruto | 4967 | 3217 | 3,83 | 84 | 8 | 64,75 | 12,29 |
| Original sem faixas mortas | 4843 | 3149 | 3,84 | 84 | 8 | 65,40 | 12,29 |
| Baseline | 1730 | 1511 | 3,46 | 22 | 6 | 53,07 | 17,08 |
| TDD | 2563 | 1788 | 3,80 | 26 | 11 | 45,99 | 9,42 |
| Rework | 2110 | 1501 | 3,27 | 19 | 7 | 43,33 | 13,20 |
| TDD com revisão (exploratório) | 2059 | 1495 | 3,95 | 29 | 8 | 45,03 | 10,89 |

## Leitura dos resultados

Todas as reconstruções têm menos NLOC que o original filtrado. Entre as
entregas, o rework tem a menor CC média nas duas ferramentas (3,06 no lizard;
3,27 no Radon). O TDD tem mais NLOC (2.563), mais funções com CC > 10 (11) e
MI mínimo menor (9,42) que a baseline. A variante com revisão fica separada
como exploratória.

Essas medidas descrevem tamanho e estrutura, não equivalência funcional.
As entregas falham em partes diferentes do gabarito: um código menor pode
omitir comportamento. A comparação tem uma run por condição e não isola o
efeito de TDD. O MI depende da divisão em módulos e não deve virar ranking
de correção. O original tem MI mediano maior mesmo com mais NLOC e uma
função com CC 84; isso mostra que as medidas capturam aspectos distintos.

As métricas de função incluem nome, arquivo e linhas no JSON, permitindo
localizar os extremos sem executar as aplicações.

Referências das ferramentas: [lizard](https://github.com/terryyin/lizard/blob/master/README.rst),
[complexidade Radon](https://github.com/rubik/radon/blob/master/radon/complexity.py)
e [MI/Halstead Radon](https://github.com/rubik/radon/blob/master/radon/metrics.py).
