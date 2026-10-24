"""Grupos modulares do v3 com o escopo e o avaliador v2. De demos/: python -m caronte.piloto_v3 [baseline|tdd|rework]."""

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from caronte.piloto_v2 import AQUI, DEMOS, RUNTIME, HarnessRework, ProjetoV2, avaliar, preparar_rework
from harness.cli import nome_do_projeto
from harness.models import Batch, HarnessDireto, HarnessTDD, Requisito

REQUISITO = DEMOS / "requisitos/05-prejanus-back-piloto-v3"
ENTRADA_REWORK = AQUI / "piloto-v3/entrada-rework"
PROVEDOR = {"only": ["novita/fp8"], "allow_fallbacks": False,
            "max_price": {"prompt": 0.7, "completion": 2.2}}


class V3:
    def agente(self, *args):
        agente = super().agente(*args)
        modelo = agente._agno.model
        modelo.max_retries = 0
        modelo.extra_body = {**modelo.extra_body, "provider": PROVEDOR}
        return agente


class BaselineV3(V3, HarnessDireto):
    pass


class TDDV3(V3, HarnessTDD):
    pass


class ReworkV3(V3, HarnessRework):
    pass


GRUPOS = {"baseline": BaselineV3, "tdd": TDDV3, "rework": ReworkV3}


def preparar_rework_v3():
    destino = preparar_rework(REQUISITO, ENTRADA_REWORK)
    secao = (REQUISITO / "requisito.md").read_text().split("## Organização obrigatória")[1].split("\n## ")[0]
    with open(destino / "requisito.md", "a") as f:
        f.write("\n## Organização obrigatória" + secao.rstrip() + "\n")
    return destino


def manifesto(raiz, requisito, grupo):
    """Separa produção, testes e o que o harness semeou, conferindo se o semeado mudou."""
    semeados = {d.name for d in requisito.anexos}
    arquivos = {}
    for p in sorted(raiz.rglob("*")):
        nome = p.relative_to(raiz)
        if not p.is_file() or {"_harness", "__pycache__"} & set(nome.parts):
            continue
        if nome.parts[0] == "tests":
            tipo = "testes_fornecidos" if grupo == "rework" else "testes_autorais"
        else:
            tipo = "infra_semeada" if nome.parts[0] in semeados else "harness" if str(nome) == "pytest.ini" else "producao"
        dados = p.read_bytes()
        arquivos[str(nome)] = {"tipo": tipo, "sha256": hashlib.sha256(dados).hexdigest(),
                               "linhas": len(dados.decode(errors="replace").splitlines())}
        if nome.parts[0] in semeados:
            arquivos[str(nome)]["semeado_alterado"] = (requisito.diretorio / nome).read_bytes() != dados
    return arquivos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("grupo", nargs="?", default="baseline", choices=GRUPOS)
    grupo = parser.parse_args().grupo
    requisito = Requisito(preparar_rework_v3() if grupo == "rework" else REQUISITO)
    raiz = DEMOS / "runs/caronte" / nome_do_projeto(REQUISITO.name, grupo)
    projeto = ProjetoV2(raiz, requisito.alvo, grupo)
    print(f"Projeto: {raiz}", flush=True)
    log = asyncio.run(GRUPOS[grupo](projeto, requisito, Batch(), com_cua=False).executar())
    entrada = projeto.saida / "entrada"
    shutil.copytree(requisito.diretorio, entrada)
    shutil.copyfile(Path(__file__), entrada / "piloto_v3.py")
    shutil.copytree(DEMOS / "harness/prompts", entrada / "prompts")
    runtime = {"imagem": RUNTIME, "orcamento": log["orcamento"], "provider": PROVEDOR,
               "context_length": 1048576,
               "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    (entrada / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    arquivos = manifesto(raiz, requisito, grupo)
    (projeto.saida / "MANIFESTO_ENTREGA.json").write_text(json.dumps(arquivos, indent=2) + "\n")
    tipos = {}
    for a in arquivos.values():
        tipos[a["tipo"]] = tipos.get(a["tipo"], 0) + 1
    print(json.dumps({"run": str(raiz), "custo_usd": log["total_cost_usd"], "arquivos": tipos,
                      "pytest_final": log["pytest_final"], "stages": log["stages"]}, ensure_ascii=False), flush=True)
    resultado = avaliar(raiz)
    print(json.dumps({k: resultado[k] for k in ("passed", "total", "visiveis", "reservados")}), flush=True)


if __name__ == "__main__":
    main()
