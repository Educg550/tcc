"""Baseline modular, mesmo escopo e avaliador v2. De demos/: python -m caronte.piloto_v3."""

import asyncio
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from caronte.piloto_v2 import DEMOS, RUNTIME, ProjetoV2, avaliar
from harness.cli import nome_do_projeto
from harness.models import Batch, HarnessDireto, Requisito

REQUISITO = DEMOS / "requisitos/05-prejanus-back-piloto-v3"
PROVEDOR = {"only": ["novita/fp8"], "allow_fallbacks": False,
            "max_price": {"prompt": 0.7, "completion": 2.2}}


class BaselineV3(HarnessDireto):
    def agente(self, *args):
        agente = super().agente(*args)
        modelo = agente._agno.model
        modelo.max_retries = 0
        modelo.extra_body = {**modelo.extra_body, "provider": PROVEDOR}
        return agente


def main():
    requisito = Requisito(REQUISITO)
    raiz = DEMOS / "runs/caronte" / nome_do_projeto(requisito.id, "baseline")
    projeto = ProjetoV2(raiz, requisito.alvo, "baseline")
    print(f"Projeto: {raiz}", flush=True)
    log = asyncio.run(BaselineV3(projeto, requisito, Batch(), com_cua=False).executar())
    entrada = projeto.saida / "entrada"
    shutil.copytree(REQUISITO, entrada)
    shutil.copyfile(Path(__file__), entrada / "piloto_v3.py")
    shutil.copytree(DEMOS / "harness/prompts", entrada / "prompts")
    runtime = {"imagem": RUNTIME, "orcamento": log["orcamento"], "provider": PROVEDOR,
               "context_length": 1048576,
               "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    (entrada / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    arquivos = log["stages"][0]["arquivos"]
    manifesto = {nome: {"sha256": hashlib.sha256((raiz / nome).read_bytes()).hexdigest(),
                        "linhas": len((raiz / nome).read_text().splitlines())} for nome in arquivos}
    (projeto.saida / "MANIFESTO_ENTREGA.json").write_text(json.dumps(manifesto, indent=2) + "\n")
    print(json.dumps({"run": str(raiz), "custo_usd": log["total_cost_usd"],
                      "arquivos": len(arquivos), "stages": log["stages"]}, ensure_ascii=False), flush=True)
    resultado = avaliar(raiz)
    print(json.dumps({k: resultado[k] for k in ("passed", "total", "visiveis", "reservados")}), flush=True)


if __name__ == "__main__":
    main()
