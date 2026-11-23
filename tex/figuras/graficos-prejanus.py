"""Gera o gráfico por área do gabarito do PreJanus-back; executar da raiz com Python e Matplotlib."""

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PASTA = Path(__file__).resolve().parent
DEMOS = PASTA.parents[1] / "demos"
RUNS = DEMOS / "runs/caronte"
EXECUCOES = {
    "Baseline": "05-prejanus-back-piloto-v3-baseline-20261023-221756",
    "TDD": "05-prejanus-back-piloto-v3-tdd-20261023-223904",
    "TDD com revisão": "05-prejanus-back-piloto-v3-tdd-revisao-20261027-161847",
    "Rework": "05-prejanus-back-piloto-v3-rework-20261024-000419",
}
CORES = ["#24557a", "#b15c25", "#6a8f3a", "#7a3f7a"]
AREAS = {"acesso": "Acesso", "avaliacao": "Avaliação", "editais": "Editais",
         "formularios": "Formulários", "inscricoes": "Inscrições", "mapeamentos": "Mapeamentos",
         "mensagens": "Mensagens", "relatorios": "Relatórios", "selecao": "Seleção"}


def area(caso):
    return caso.get("classname").rsplit(".test_", 1)[1]


casos, acertos = Counter(), {}
for grupo, pasta in EXECUCOES.items():
    raiz = ET.parse(RUNS / pasta / "_harness/oraculo.xml").getroot()
    todos = list(raiz.iter("testcase"))
    assert len(todos) == 247
    casos = Counter(area(c) for c in todos)
    acertos[grupo] = Counter(area(c) for c in todos if len(c) == 0)
    assert sum(acertos[grupo].values()) == json.loads((RUNS / pasta / "_harness/ORACULO.json").read_text())["passed"]

divergencias = json.loads((DEMOS / "caronte/piloto-v2/gabarito/divergencias.json").read_text())
falhas_original = Counter(t.split(".py")[0][5:] for a in divergencias["achados"].values() for t in a["testes"])
original = {a: casos[a] - falhas_original[a] for a in casos}
assert sum(original.values()) == 233
assert [sum(acertos[g].values()) for g in EXECUCOES] == [186, 140, 194, 211]

# Percursos e Rastreio têm um caso cada e ficam fora do gráfico.
fig, ax = plt.subplots(figsize=(10, 4.2))
largura = 0.18
for i, (grupo, cor) in enumerate(zip(EXECUCOES, CORES)):
    ax.bar([j + (i - 1.5) * largura for j in range(len(AREAS))],
           [100 * acertos[grupo][a] / casos[a] for a in AREAS], largura, color=cor, label=grupo)
ax.scatter(range(len(AREAS)), [100 * original[a] / casos[a] for a in AREAS],
           marker="_", s=500, color="black", zorder=3, label="Original")
ax.set(xticks=range(len(AREAS)), xticklabels=[f"{r}\n({casos[a]})" for a, r in AREAS.items()],
       ylim=(0, 105), ylabel="Casos aprovados (%)")
ax.tick_params(axis="x", labelsize=8)
ax.grid(axis="y", alpha=.2)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=5, frameon=False)
fig.tight_layout()
fig.savefig(PASTA / "prejanus-areas.pdf")
plt.close(fig)

for a in [*AREAS, "percursos", "rastreio"]:
    print(a, casos[a], original[a], *(acertos[g][a] for g in EXECUCOES))
