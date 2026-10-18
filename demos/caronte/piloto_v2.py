"""Grupos do piloto v2 no ambiente isolado. De demos/: python -m caronte.piloto_v2 baseline|tdd|rework|avaliar."""

import argparse
import ast
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path

import yaml

from harness.cli import nome_do_projeto
from harness.models.dominio import Projeto, Requisito, ResultadoPytest
from harness.models.etapas import EtapaTDD
from harness.models.harness import Harness, HarnessDireto, HarnessTDD
from harness.models.politicas import Batch

AQUI = Path(__file__).resolve().parent
V2 = AQUI / "piloto-v2"
sys.path.insert(0, str(V2))
from ambiente import DC, ESTADO, URL, dc, esperar, limpar_esquema, restaurar  # noqa: E402

DEMOS = AQUI.parent
REQUISITO = DEMOS / "requisitos/03-caronte-prejanus-completo"
RUNTIME = "sha256:e10c92c97762c4c419297360e59d245bfa36db080e07e1d77beb9e11ee4b934c"
BACKENDS = ("prejanus-back", "local", "sem-atalho")
SPLIT = json.loads((V2 / "oraculo/split.json").read_text())
VISIVEIS = sorted({i.split("[")[0] for i in SPLIT["visiveis"]})


def override(raiz):
    servico = {"image": RUNTIME, "read_only": True, "tmpfs": ["/tmp", "/workspace/_harness"],
               "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"],
               "command": ["uvicorn", "app:app", "--app-dir", "/workspace", "--host", "0.0.0.0", "--port", "8000"],
               "volumes": [f"{raiz}:/workspace:ro"]}
    return {"services": {nome: servico for nome in BACKENDS}}


@contextmanager
def candidato(raiz, saida):
    """Troca os três backends do ambiente pelo app gerado e devolve o original ao sair."""
    (raiz / "_harness").mkdir(exist_ok=True)
    arquivo = saida / "compose.candidato.yml"
    saida.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(yaml.safe_dump(override(raiz)))
    com = ["-f", str(V2 / "compose.yml"), "-f", str(arquivo)]
    limpar_esquema()
    subprocess.run([*DC, *com[2:], "up", "-d", "--force-recreate", *BACKENDS], check=True, capture_output=True)
    # O nginx resolve os upstreams só ao subir; recriados, os backends trocam de IP.
    dc("restart", "proxy")
    try:
        try:
            for caminho in ("/backend/", "/local/", "/sem-atalho/"):
                esperar(URL + caminho, tentativas=120)
        except RuntimeError:
            pass  # app que não sobe reprova nos testes, com o log anexado ao gate
        restaurar()
        yield
    finally:
        for nome in BACKENDS:
            log = subprocess.run([*DC, "logs", "--no-color", nome], capture_output=True)
            (saida / f"app-{nome}.log").write_bytes(log.stdout + log.stderr)
        dc("up", "-d", "--force-recreate", *BACKENDS)
        dc("restart", "proxy")
        limpar_esquema()


def pytest_oraculo(saida, nome, ids=()):
    alvos = [str(V2 / "oraculo" / i) for i in ids] or [str(V2 / "oraculo")]
    cmd = [sys.executable, "-m", "pytest", *alvos, "-q", "--tb=short", "-p", "no:cacheprovider",
           f"--junitxml={saida / (nome + '.xml')}"]
    return subprocess.run(cmd, cwd=DEMOS, capture_output=True, text=True)


class ProjetoV2(Projeto):
    def __init__(self, raiz, alvo, grupo):
        super().__init__(raiz, alvo)
        self.grupo, self.gates = grupo, 0

    def rodar_pytest(self):
        self.gates += 1
        with candidato(self.raiz, self.saida):
            if self.grupo == "rework":
                # Executa a cópia do avaliador, não a do workspace: editar testes não muda o gate.
                r = pytest_oraculo(self.saida, f"gate-{self.gates}", VISIVEIS)
            else:
                r = subprocess.run(
                    ["docker", "run", "--rm", "--network", "caronte-piloto-v2_default", "--read-only", "--tmpfs", "/tmp",
                     "--cap-drop=ALL", "--security-opt=no-new-privileges", "-e", "PYTHONDONTWRITEBYTECODE=1",
                     "-e", "CARONTE_API=http://local:8000", "-e", "CARONTE_API_SEM_ATALHO=http://sem-atalho:8000",
                     "-v", f"{self.raiz}:/workspace:ro", "--mount", "type=tmpfs,dst=/workspace/_harness",
                     "-w", "/workspace", RUNTIME, "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
                    capture_output=True, text=True)
        saida = r.stdout + "\n" + r.stderr
        if r.returncode:
            saida += "\n" + "\n".join(p.read_text(errors="replace")[-4000:] for p in sorted(self.saida.glob("app-*.log")))
        (self.saida / f"pytest-{self.gates}.txt").write_text(saida)
        return ResultadoPytest.de_saida(saida, r.returncode == 0)


def avaliar(raiz):
    """Oráculo inteiro depois da geração; nada volta para a sessão."""
    saida = raiz / "_harness"
    with candidato(raiz, saida):
        r = pytest_oraculo(saida, "oraculo")
    (saida / "oraculo.txt").write_text(r.stdout + "\n" + r.stderr)
    casos = {f"{Path(t.get('classname').replace('.', '/')).name}.py::{t.get('name')}":
             t.find("failure") is None and t.find("error") is None
             for t in ET.parse(saida / "oraculo.xml").iter("testcase")}
    resultado = {"passed": sum(casos.values()), "total": len(casos), "runtime_image": RUNTIME,
                 "relatorio": json.loads((ESTADO / "ORACULO.json").read_text())}
    for grupo in ("visiveis", "reservados"):
        selecionados = [casos[i] for i in SPLIT[grupo]]
        resultado[grupo] = {"passed": sum(selecionados), "total": len(selecionados)}
    resultado["fontes_sha256"] = {str(p.relative_to(raiz)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in raiz.rglob("*.py") if "_harness" not in p.relative_to(raiz).parts}
    (saida / "ORACULO.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    return resultado


def preparar_rework():
    destino = V2 / "entrada-rework"
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(REQUISITO, destino)
    texto = (destino / "alvo.toml").read_text().replace("../../caronte/skills.lock.json", "../../skills.lock.json")
    (destino / "alvo.toml").write_text(texto)
    (destino / "requisito.md").write_text((V2 / "rework.md").read_text())
    testes = destino / "tests"
    testes.mkdir()
    visiveis = {}
    for i in VISIVEIS:
        arquivo, funcao = i.split("::")
        visiveis.setdefault(arquivo, set()).add(funcao)
    for arquivo, funcoes in visiveis.items():
        modulo = ast.parse((V2 / "oraculo" / arquivo).read_text())
        modulo.body = [n for n in modulo.body if not (isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                                                      and n.name not in funcoes)]
        (testes / arquivo).write_text(ast.unparse(modulo) + "\n")
    for nome in ("conftest.py",):
        shutil.copyfile(V2 / "oraculo" / nome, testes / nome)
    shutil.copyfile(V2 / "ambiente.py", testes / "ambiente.py")
    return destino


class HarnessRework(Harness):
    grupo = "rework"

    async def etapas(self):
        codigo = self.etapa("code", self.agente("coder", self.requisito.modelos["coder"], EtapaTDD), EtapaTDD)
        return [await codigo.executar(self.prompt("## TESTES A FAZER PASSAR\n\n" + self.projeto.contexto("tests")), self.projeto)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("grupo", choices=("baseline", "tdd", "rework", "avaliar"))
    parser.add_argument("projeto", nargs="?", help="pasta da run, para avaliar")
    args = parser.parse_args()
    if args.grupo == "avaliar":
        r = avaliar(Path(args.projeto).resolve())
        print(json.dumps({k: r[k] for k in ("passed", "total", "visiveis", "reservados")}))
        return
    classe = {"baseline": HarnessDireto, "tdd": HarnessTDD, "rework": HarnessRework}[args.grupo]
    req = Requisito(REQUISITO if args.grupo != "rework" else preparar_rework())
    raiz = DEMOS / "runs/caronte" / nome_do_projeto("03-caronte-prejanus-completo", classe.grupo)
    projeto = ProjetoV2(raiz, req.alvo, args.grupo)
    log = asyncio.run(classe(projeto, req, Batch(), com_cua=False).executar())
    entrada = projeto.saida / "entrada"
    shutil.copytree(req.diretorio, entrada, ignore=shutil.ignore_patterns("infra", "tests"))
    shutil.copyfile(Path(__file__), entrada / "piloto_v2.py")
    (entrada / "runtime.json").write_text(json.dumps({"imagem": RUNTIME, "orcamento": log["orcamento"]}, indent=2))
    print(json.dumps({"run": str(raiz), "custo_usd": log["total_cost_usd"], "pytest": log["pytest_final"],
                      "etapas": [(s["id"], s["motivo"]) for s in log["stages"]]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
