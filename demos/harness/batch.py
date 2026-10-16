import asyncio
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
    # Uma de cada vez: o custo de cada passo é o delta de uso da chave, e runs em
    # paralelo somariam o gasto umas das outras.
    for args in pendentes:
        rodar(*args)


if __name__ == "__main__":
    load_dotenv(DEMOS / ".env")
    executar()
