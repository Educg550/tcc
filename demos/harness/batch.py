import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import mkdtemp

from dotenv import load_dotenv

from .models import Batch, HarnessDireto, HarnessTDD, Projeto, Requisito

DEMOS = Path(__file__).resolve().parent.parent
PROVIDERS = ("deepseek", "glm")


def rodar(classe, projeto: Projeto, requisito: Requisito) -> None:
    print(f"executando: {projeto.raiz}", flush=True)
    asyncio.run(classe(projeto, requisito, Batch(), com_cua=False).executar())


def executar(destino: Path = DEMOS / "runs" / "batch") -> None:
    pendentes = []
    for provider in PROVIDERS:
        requisito = Requisito(DEMOS / "requisitos" / f"01-formulario-docentes-{provider}")
        for numero in range(1, 51):
            for classe in (HarnessTDD, HarnessDireto):
                raiz = destino / provider / f"run{numero}" / classe.grupo
                projeto = Projeto(raiz, requisito.alvo)
                if (projeto.saida / "RUN.log").is_file():
                    print(f"já registrada: {raiz}", flush=True)
                    continue
                if raiz.exists() and any(raiz.iterdir()):
                    arquivo = Path(mkdtemp(prefix=f"{classe.grupo}-interrompida-", dir=raiz.parent))
                    raiz.rename(arquivo / classe.grupo)
                    print(f"tentativa incompleta preservada: {arquivo}", flush=True)
                pendentes.append((classe, projeto, requisito))
    with ThreadPoolExecutor(max_workers=25) as pool:
        for inicio in range(0, len(pendentes), 25):
            lote = [pool.submit(rodar, *args) for args in pendentes[inicio:inicio + 25]]
            for run in lote:
                run.result()


if __name__ == "__main__":
    load_dotenv(DEMOS / ".env")
    executar()
