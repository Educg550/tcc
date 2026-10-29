"""MEDIDAS.json por etapa/sessão de uma run v3. Uso: python medidas.py <run>"""
import ast
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

raiz = Path(sys.argv[1])
h = raiz / "_harness"
log = json.loads((h / "RUN.log").read_text())
fins = [json.loads(l) for l in (h / "chamadas_modelo.jsonl").read_text().splitlines()]
fins = [e for e in fins if e["evento"] == "fim"]
sessoes = list(dict.fromkeys(e["session_id"] for e in fins))
etapas = []
for stage, sessao in zip(log["stages"], sessoes):
    cs = [e for e in fins if e["session_id"] == sessao]
    m = [e["metricas"] for e in cs]
    etapas.append({
        "etapa": stage["id"], "sessao": sessao, "motivo": stage["motivo"], "duracao_s": stage["duration_s"],
        "propostas": stage["passos"], "retries": stage["retries"], "chamadas_modelo": len(cs),
        "cost_usd": round(sum(x["cost"] for x in m), 7),
        "input_tokens": sum(x["input_tokens"] for x in m), "output_tokens": sum(x["output_tokens"] for x in m),
        "total_tokens": sum(x["total_tokens"] for x in m),
        "cache_read_tokens": sum(x.get("cache_read_tokens", 0) for x in m),
        "primeira_entrada_tokens": m[0]["input_tokens"],
        "contexto_pico_tokens": max(x["input_tokens"] for x in m),
        "contexto_pico_pct": round(100 * max(x["input_tokens"] for x in m) / 1048576, 2),
        "entrada_saida_pico_tokens": max(x["input_tokens"] + x["output_tokens"] for x in m),
        "request_max_bytes": max(e["request_bytes"] for e in cs),
        "entrada_por_chamada": [x["input_tokens"] for x in m],
        "ferramentas": Counter(f for e in cs for f in e["ferramentas"]),
        "pytest_por_proposta": stage.get("historico", []),
        "tests_vermelhos_no_inicio": stage.get("tests_vermelhos"),
    })
manifesto = json.loads((h / "MANIFESTO_ENTREGA.json").read_text())
por_tipo = {}
for nome, a in manifesto.items():
    t = por_tipo.setdefault(a["tipo"], {"arquivos": 0, "linhas": 0, "python": 0, "linhas_python": 0})
    t["arquivos"] += 1
    t["linhas"] += a["linhas"]
    if nome.endswith(".py"):
        t["python"] += 1
        t["linhas_python"] += a["linhas"]
testes_autorais = sum(
    sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in ast.walk(ast.parse((raiz / n).read_text())))
    for n, a in manifesto.items() if a["tipo"] == "testes_autorais" and n.endswith(".py"))
nome_gabarito = "gabarito" if (h / "GABARITO.json").exists() else "oraculo"
gabarito = json.loads((h / f"{nome_gabarito.upper()}.json").read_text())
casos = {f"{Path(t.get('classname').replace('.', '/')).name}.py::{t.get('name')}":
         "failure" if t.find("failure") is not None else "error" if t.find("error") is not None else "passed"
         for t in ET.parse(h / f"{nome_gabarito}.xml").iter("testcase")}
comport = {k: v for k, v in casos.items() if not k.startswith("test_rastreio")}
intactos = all(gabarito["fontes_sha256"].get(n) == a["sha256"] for n, a in manifesto.items() if n.endswith(".py"))
medidas = {
    "run": raiz.name, "grupo": log["grupo"], "run_s": log["total_duration_s"], "cost_usd": log["total_cost_usd"],
    "total_tokens": log["total_tokens"], "pytest_final_proprio": log["pytest_final"],
    "integridade_testes": log["integridade"], "etapas": etapas, "arquivos": por_tipo,
    "funcoes_teste_autorais": testes_autorais,
    "maiores_modulos_producao": sorted(((n, a["linhas"]) for n, a in manifesto.items() if a["tipo"] == "producao"),
                                       key=lambda x: -x[1])[:5],
    "semeado_alterado": [n for n, a in manifesto.items() if a.get("semeado_alterado")],
    "gabarito": {"passed": gabarito["passed"], "total": gabarito["total"], "visiveis": gabarito["visiveis"],
                "reservados": gabarito["reservados"], "resultado": Counter(casos.values()),
                "comportamentais": {"passed": sum(v == "passed" for v in comport.values()), "total": len(comport)},
                "rastreabilidade": {"passed": sum(v == "passed" for k, v in casos.items() if k not in comport),
                                    "total": len(casos) - len(comport)},
                "operacoes_exercitadas": gabarito["relatorio"]["operacoes_exercitadas"]},
    "hashes_intactos_depois_gabarito": intactos,
}
(h / "MEDIDAS.json").write_text(json.dumps(medidas, ensure_ascii=False, indent=1) + "\n")
print(json.dumps({k: v for k, v in medidas.items() if k != "etapas"}, ensure_ascii=False, indent=1))
for e in etapas:
    print(json.dumps({k: v for k, v in e.items() if k != "entrada_por_chamada"}, ensure_ascii=False))
