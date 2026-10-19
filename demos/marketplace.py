"""Uma sessão GLM para o smoke de escala. De demos/: python -m marketplace."""

import asyncio
import json
import shutil
from pathlib import Path

from harness.cli import nome_do_projeto
from harness.models import Batch, HarnessDireto, Projeto, Requisito

DEMOS = Path(__file__).resolve().parent
REQUISITO = DEMOS / "requisitos/04-marketplace-glm"


class Marketplace(HarnessDireto):
    def agente(self, *args):
        agente = super().agente(*args)
        modelo = agente._agno.model
        modelo.max_retries = 0
        modelo.extra_body = {
            **modelo.extra_body,
            "provider": {"only": ["novita/fp8"], "allow_fallbacks": False,
                         "max_price": {"prompt": 0.7, "completion": 2.2}},
        }
        return agente


def main():
    requisito = Requisito(REQUISITO)
    projeto = Projeto(DEMOS / "runs/marketplace" / nome_do_projeto(requisito.id, "baseline"), requisito.alvo)
    print(f"Projeto: {projeto.raiz}", flush=True)
    resultado = asyncio.run(Marketplace(projeto, requisito, Batch(), com_cua=False).executar())
    shutil.copytree(REQUISITO, projeto.saida / "entrada")
    print(json.dumps(resultado, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
