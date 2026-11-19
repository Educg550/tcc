"""Gera as figuras do lote preservado; executar da raiz com Python e Matplotlib."""

import json
from math import isclose, sqrt
from pathlib import Path
from statistics import NormalDist, median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PASTA = Path(__file__).resolve().parent
LOTE = PASTA.parents[1] / "demos/runs/batch"
CELULAS = [(modelo, grupo) for modelo in ("deepseek", "glm") for grupo in ("baseline", "tdd")]
ROTULOS = ["DeepSeek\nbaseline", "DeepSeek\nTDD", "GLM\nbaseline", "GLM\nTDD"]
CORES = ["#24557a", "#b15c25", "#24557a", "#b15c25"]
Z = NormalDist().inv_cdf(0.975)


def wilson(x, n):
    p = x / n
    centro = (p + Z**2 / (2 * n)) / (1 + Z**2 / n)
    raio = Z * sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / (1 + Z**2 / n)
    return centro - raio, centro + raio


assert isclose(wilson(25, 50)[0], 0.3664451431682858)
assert isclose(wilson(0, 50)[0], 0, abs_tol=1e-12)
assert isclose(wilson(50, 50)[1], 1)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

logs = {}
for modelo, grupo in CELULAS:
    arquivos = sorted((LOTE / modelo).glob(f"run*/{grupo}/_harness/RUN.log"))
    assert len(arquivos) == 50
    logs[modelo, grupo] = [json.loads(p.read_text()) for p in arquivos]

canonica = json.loads((LOTE / "cypress.json").read_text())
extras = json.loads((LOTE / "cypress-extra.json").read_text())
assert len(canonica) == 153 and len(extras) == 94
assert all(len(x["criterios"]) == 12 for x in canonica)
assert all(len(x["criterios"]) == 10 for x in extras)
aprovadas = {x["run"] for x in canonica if all(c["passou"] for c in x["criterios"])}
com_extras = {x["run"] for x in extras if all(c["passou"] for c in x["criterios"])}
assert com_extras <= aprovadas
assert len(aprovadas) == 94 and len(com_extras) == 81

fig, ax = plt.subplots(figsize=(8, 4.1))
for conjunto, deslocamento, marcador, cor, legenda in (
    (aprovadas, -0.12, "o", "#24557a", "12 critérios iniciais"),
    (com_extras, 0.12, "s", "#b15c25", "12 iniciais + 10 extras"),
):
    contagens = [sum(r.startswith(m + "/") and r.endswith("/" + g) for r in conjunto) for m, g in CELULAS]
    assert contagens == ([41, 38, 3, 12] if conjunto is aprovadas else [39, 30, 3, 9])
    for i, x in enumerate(contagens):
        lo, hi = wilson(x, 50)
        ax.errorbar(i + deslocamento, 100*x/50, yerr=[[100*(x/50-lo)], [100*(hi-x/50)]],
                    fmt=marcador, color=cor, capsize=4, label=legenda if i == 0 else None)
ax.set(xticks=range(4), xticklabels=ROTULOS, ylim=(0, 101), ylabel="Execuções aprovadas (%)")
ax.grid(axis="y", alpha=.2)
ax.legend(loc="upper right", frameon=False)
fig.tight_layout()
fig.savefig(PASTA / "formulario-aprovacao.pdf")
plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(10, 4))
for ax, campo, divisor, titulo in zip(axes, ("total_cost_usd", "total_duration_s", "total_tokens"),
                                    (1, 60, 1000), ("Custo (US$)", "Duração (min)", "Tokens (mil)")):
    valores = [[r[campo]/divisor for r in logs[c] if r[campo] is not None] for c in CELULAS]
    assert all(len(v) == 50 and all(x > 0 for x in v) for v in valores)
    caixas = ax.boxplot(valores, patch_artist=True, showfliers=False, widths=.55)
    for i, (v, caixa) in enumerate(zip(valores, caixas["boxes"])):
        caixa.set(facecolor=CORES[i], alpha=.25)
        ax.scatter([i+1 + ((j*17 % 49)/48-.5)*.3 for j in range(50)], v,
                   color=CORES[i], s=9, alpha=.6, zorder=3)
    ax.set(yscale="log", title=titulo, xticks=range(1, 5), xticklabels=ROTULOS)
    ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="y", alpha=.2)
fig.tight_layout()
fig.savefig(PASTA / "formulario-recursos.pdf")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.3))
ns = range(10, 501, 2)
ax.plot(ns, [100*(wilson(n/2, n)[1] - .5) for n in ns], color="#24557a")
for n in (50, 100, 200):
    h = 100*(wilson(n/2, n)[1] - .5)
    ax.plot(n, h, "o", color="#b15c25")
    ax.annotate(f"n={n}: {h:.1f} p.p.".replace(".", ",", 1), (n, h), xytext=(8, 8), textcoords="offset points")
ax.set(xlabel="Execuções por célula", ylabel="Semilargura do IC de 95% (p.p.)", ylim=(0, 31))
ax.grid(alpha=.2)
fig.tight_layout()
fig.savefig(PASTA / "formulario-precisao.pdf")
plt.close(fig)

for c in CELULAS:
    print(c, "custo total", round(sum(r["total_cost_usd"] for r in logs[c]), 4),
          "mediana", round(median(r["total_cost_usd"] for r in logs[c]), 4))
