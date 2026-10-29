"""TDD/rework do piloto congelado. De demos/: python -m caronte.piloto tdd|rework."""

import argparse
import ast
import asyncio
import copy
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from contextlib import ExitStack, contextmanager
from dataclasses import replace
from pathlib import Path

import httpx

from harness.cli import nome_do_projeto
from harness.models.dominio import Projeto, Requisito, ResultadoPytest
from harness.models.etapas import EtapaTDD
from harness.models.harness import Harness, HarnessTDD
from harness.models.politicas import Batch

AQUI = Path(__file__).resolve().parent
DEMOS = AQUI.parent
REQUISITO = DEMOS / "requisitos/02-caronte-consulta"
BASELINE = DEMOS / "runs/caronte/02-caronte-consulta-baseline-20261017-100205"
RUNTIME = "sha256:de2233fd51964447ae4dc633d2898930ac80b0c581b6b99101feb1eec3fc70b9"


def materializar_visiveis():
    """Especializa apenas os casos visíveis, sem entregar parametrizações reservadas."""
    fonte = ast.parse((AQUI / "gabarito/test_consulta.py").read_text())
    funcoes = {n.name: n for n in fonte.body if isinstance(n, ast.FunctionDef)}
    ids = json.loads((AQUI / "gabarito/split.json").read_text())["visiveis"]
    saida = ["import pytest\nfrom dados import CARONTE, respostas_da_fixture, secoes_do_formulario\n"
             'CANDIDATA = "Ana Piloto Caronte"\nEMAIL = "candidata.piloto@example.com"\n']
    for i, id in enumerate(ids):
        nome, _, valor = id.split("::")[-1].partition("[")
        f = copy.deepcopy(funcoes[nome])
        f.name = f"{nome}_visivel_{i:02d}"
        for d in list(f.decorator_list):
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "parametrize":
                parametro = ast.literal_eval(d.args[0])
                literal = valor[:-1]
                literal = int(literal) if parametro == "secao" else literal
                f.args.args = [a for a in f.args.args if a.arg != parametro]
                f.body.insert(0, ast.Assign(targets=[ast.Name(id=parametro, ctx=ast.Store())], value=ast.Constant(literal)))
                f.decorator_list.remove(d)
        saida.append(ast.unparse(ast.fix_missing_locations(f)))
    texto = "\n\n".join(saida) + "\n"
    assert len(ids) == 20 and sum(isinstance(n, ast.FunctionDef) for n in ast.parse(texto).body) == 20
    return texto


class ProjetoPiloto(Projeto):
    def __init__(self, raiz, alvo, grupo):
        super().__init__(raiz, alvo)
        self.grupo, self.gates, self.servidores = grupo, 0, 0

    def runtime(self, atalho=True):
        banco = f"{self.grupo}_20261017"
        return ["docker", "run", "--network", "shared_network", "--read-only", "--tmpfs", "/tmp",
                "--user", f"{os.getuid()}:{os.getgid()}", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", f"APP_ENV={'local' if atalho else 'sem-atalho'}",
                "-e", "DEV_USER_ID=2",
                "-e", f"DB_CONNECTION_STRING=postgresql+psycopg://caronte_prejanus:caronte_prejanus@db:5432/caronte_prejanus_{banco}",
                "-e", f"DB_CONNECTION_STRING_FORMS=postgresql+psycopg://caronte_forms_reader:caronte_forms_reader@db:5432/caronte_forms_{banco}",
                "-v", f"{self.raiz}:/workspace:ro", "--mount", "type=tmpfs,dst=/workspace/_harness",
                "-v", f"{AQUI / 'uploads-consulta'}:/shared/uploads:ro", "-w", "/workspace"]

    @contextmanager
    def servidor(self, atalho=True):
        self.servidores += 1
        numero = self.servidores
        nome = f"piloto-{hashlib.sha256(str(self.raiz).encode()).hexdigest()[:8]}-{numero}"
        cmd = self.runtime(atalho) + ["-d", "--name", nome, "-p", "127.0.0.1::8000", RUNTIME,
                                      "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
        subprocess.run(cmd, check=True, capture_output=True)
        try:
            porta = subprocess.run(["docker", "port", nome, "8000"], capture_output=True, text=True).stdout.strip().rsplit(":", 1)[-1] or "0"
            url = f"http://localhost:{porta}"
            for _ in range(50):
                try:
                    if httpx.get(url, timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    if subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", nome], text=True).strip() == "false":
                        break
                time.sleep(.1)
            yield url, f"http://{nome}:8000"
        finally:
            log = subprocess.run(["docker", "logs", nome], capture_output=True)
            self.saida.mkdir(parents=True, exist_ok=True)
            (self.saida / f"app-{numero}.log").write_bytes(log.stdout + log.stderr)
            subprocess.run(["docker", "rm", "-f", nome], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def rodar_pytest(self):
        self.gates += 1
        extras = []
        with ExitStack() as stack:
            for atalho, variavel in ((True, "CARONTE_API"), (False, "CARONTE_API_SEM_ATALHO")):
                _, url = stack.enter_context(self.servidor(atalho))
                extras += ["-e", f"{variavel}={url}"]
            cmd = self.runtime() + ["--rm", *extras, RUNTIME, *shlex.split(self.alvo.comando_teste), "-p", "no:cacheprovider"]
            r = subprocess.run(cmd, capture_output=True, text=True)
        saida = r.stdout + "\n" + r.stderr
        if r.returncode:
            saida += "\n" + "\n".join(p.read_text() for p in sorted(self.saida.glob("app-*.log"))[-2:])
        self.saida.mkdir(parents=True, exist_ok=True)
        (self.saida / f"pytest-{self.gates}.txt").write_text(saida)
        return ResultadoPytest.de_saida(saida, r.returncode == 0)


class HarnessRework(Harness):
    grupo = "rework"

    async def etapas(self):
        codigo = self.etapa("code", self.agente("coder", self.requisito.modelos["coder"], EtapaTDD), EtapaTDD)
        return [await codigo.executar(self.prompt("## TESTES A FAZER PASSAR\n\n" + self.projeto.contexto("tests")), self.projeto)]


def preparar_rework():
    destino = AQUI / "entrada-rework"
    destino.mkdir(exist_ok=True)
    shutil.copyfile(REQUISITO / "alvo.toml", destino / "alvo.toml")
    texto = (destino / "alvo.toml").read_text().replace('../../caronte/skills.lock.json', '../skills.lock.json')
    (destino / "alvo.toml").write_text(texto)
    shutil.copytree(REQUISITO / "infra", destino / "infra", dirs_exist_ok=True)
    # Só contrato operacional: o comportamento do rework vem dos testes visíveis.
    infra = (REQUISITO / "infra/README.md").read_text().split("`GET /` deve responder")[0]
    (destino / "infra/README.md").write_text(infra)
    (destino / "requisito.md").write_text((AQUI / "prompts/rework.md").read_text())
    testes = destino / "tests"
    testes.mkdir(exist_ok=True)
    (testes / "test_consulta.py").write_text(materializar_visiveis())
    shutil.copyfile(AQUI / "gabarito/conftest.py", testes / "conftest.py")
    dados = (AQUI / "gabarito/dados.py").read_text().replace('Path(__file__).parent.parent', 'Path(__file__).parent / "dados"')
    (testes / "dados.py").write_text(dados)
    (testes / "dados/uploads-consulta").mkdir(parents=True, exist_ok=True)
    for nome in ("fixture-consulta-forms.sql", "formulario-mestrado.json"):
        shutil.copyfile(AQUI / nome, testes / "dados" / nome)
    visiveis = json.loads((AQUI / "gabarito/split.json").read_text())["visiveis"]
    for id in visiveis:
        if "test_baixa_o_anexo[" in id:
            nome = id.split("[", 1)[1][:-1]
            shutil.copyfile(AQUI / "uploads-consulta" / nome, testes / "dados/uploads-consulta" / nome)
    return destino


def avaliar(projeto):
    """Gabarito externo após a geração; nenhum resultado volta para a sessão."""
    anteriores = [int(p.stem.split("-")[-1]) for p in projeto.saida.glob("app-[0-9]*.log")]
    projeto.servidores = max(anteriores, default=0)
    with projeto.servidor(True) as (url, _), projeto.servidor(False) as (sem_atalho, _):
        cmd = [sys.executable, "-m", "pytest", str(AQUI / "gabarito"), "-q", "--tb=short",
               f"--junitxml={projeto.saida / 'gabarito.xml'}"]
        r = subprocess.run(cmd, cwd=DEMOS, env={**os.environ, "CARONTE_API": url,
                           "CARONTE_API_SEM_ATALHO": sem_atalho}, capture_output=True, text=True)
    (projeto.saida / "gabarito.txt").write_text(r.stdout + "\n" + r.stderr)
    casos = [{"nome": t.get("name"), "passou": t.find("failure") is None and t.find("error") is None}
             for t in ET.parse(projeto.saida / "gabarito.xml").iter("testcase")]
    split = json.loads((AQUI / "gabarito/split.json").read_text())
    resultado = {"instrumento": "pytest/httpx externo", "aprovado_geral": all(t["passou"] for t in casos),
                 "passed": sum(t["passou"] for t in casos), "failed": sum(not t["passou"] for t in casos),
                 "total": len(casos), "casos": casos, "runtime_image": RUNTIME}
    assert len(casos) == 28
    for grupo in ("visiveis", "reservados"):
        nomes = {id.split("::")[-1] for id in split[grupo]}
        selecionados = [t for t in casos if t["nome"] in nomes]
        assert len(selecionados) == len(nomes)
        resultado[grupo] = {"passed": sum(t["passou"] for t in selecionados), "total": len(selecionados)}
    fontes = {str(p.relative_to(projeto.raiz)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in projeto.raiz.rglob("*.py") if "_harness" not in p.relative_to(projeto.raiz).parts}
    resultado["fontes_sha256"] = fontes
    (projeto.saida / "GABARITO.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("grupo", choices=("tdd", "rework"))
    grupo = parser.parse_args().grupo
    req = Requisito(REQUISITO if grupo == "tdd" else preparar_rework())
    raiz = DEMOS / "runs/caronte" / nome_do_projeto("02-caronte-consulta", grupo)
    projeto = ProjetoPiloto(raiz, req.alvo, grupo)
    classe = HarnessTDD if grupo == "tdd" else HarnessRework
    harness = classe(projeto, req, Batch(), com_cua=False)
    harness.orcamento = replace(req.orcamento, passos=12)
    log = asyncio.run(harness.executar())
    entrada = projeto.saida / "entrada"
    entrada.mkdir()
    for nome in ("requisito.md", "alvo.toml"):
        shutil.copyfile(req.diretorio / nome, entrada / nome)
    config = (entrada / "alvo.toml").read_text().replace("passos = 1\n", "passos = 12\n")
    config = config.replace("# Esta primeira execução é somente baseline: uma sessão, sem feedback ou reexecução.", "# Orçamento por etapa da execução TDD/rework.")
    (entrada / "alvo.toml").write_text(config)
    shutil.copyfile(Path(__file__), entrada / "piloto.py")
    shutil.copyfile(AQUI / "skills.lock.json", entrada / "skills.lock.json")
    (entrada / "runtime.json").write_text(json.dumps({"imagem": RUNTIME, "bancos": f"{grupo}_20261017", "orcamento": log["orcamento"]}, indent=2))
    print(json.dumps({"run": str(raiz), "custo_usd": log["total_cost_usd"], "pytest": log["pytest_final"], "etapas": [(s["id"], s["motivo"]) for s in log["stages"]]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
