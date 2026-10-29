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
from dataclasses import replace
from pathlib import Path

import httpx
import yaml

from harness.cli import nome_do_projeto
from harness.models.dominio import Projeto, Requisito, ResultadoPytest
from harness.models.etapas import EtapaTDD
from harness.models.harness import Harness, HarnessDireto, HarnessTDD
from harness.models.politicas import Batch

AQUI = Path(__file__).resolve().parent
V2 = AQUI / "piloto-v2"
sys.path.insert(0, str(V2))
from ambiente import BACKENDS, CAMINHOS, DC, ESTADO, URL, dc, esperar, limpar_esquema, restaurar  # noqa: E402

DEMOS = AQUI.parent
REQUISITO = DEMOS / "requisitos/03-caronte-prejanus-completo"
RUNTIME = "sha256:e10c92c97762c4c419297360e59d245bfa36db080e07e1d77beb9e11ee4b934c"
SPLIT = json.loads((V2 / "gabarito/split.json").read_text())
VISIVEIS = sorted({i.split("[")[0] for i in SPLIT["visiveis"]})
# Os testes do test-writer alcançam as mesmas instâncias, provedor OAuth e caixa SMTP que o gabarito.
GATE_TDD = {"CARONTE_API": "http://local:8000", "CARONTE_API_SEM_ATALHO": "http://sem-atalho:8000",
            "CARONTE_API_SENHAUNICA": "http://prejanus-back:8000", "SENHAUNICA_PROVEDOR": "http://oauth:8000",
            "CARONTE_SMTP_API": "http://smtp:80",
            **{f"CARONTE_API_{p.upper()}": f"http://local-{p}:8000"
               for p in ("admin", "outro", "secretaria", "coordenador", "estudante")}}


def override(raiz):
    servico = {"image": RUNTIME, "read_only": True, "tmpfs": ["/tmp", "/workspace/_harness"],
               "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"],
               "command": ["uvicorn", "app:app", "--app-dir", "/workspace", "--host", "0.0.0.0", "--port", "8000"],
               "volumes": [f"{raiz}:/workspace:ro"]}
    return {"services": {nome: servico for nome in BACKENDS}}


def no_ar(tentativas=120):
    """Espera os backends; desiste quando um contêiner sai, como num erro de import."""
    for _ in range(tentativas):
        if dc("ps", "-q", "--status", "exited", *BACKENDS).stdout.strip():
            return False
        try:
            for caminho in CAMINHOS:
                esperar(URL + caminho, tentativas=1)
            return True
        except RuntimeError:
            pass
    return False


@contextmanager
def candidato(raiz, saida):
    """Troca os backends do ambiente pelo app gerado e devolve o original ao sair."""
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
        subiu = no_ar()
        restaurar()
        httpx.delete("http://localhost:8182/api/Messages/*").raise_for_status()
        yield subiu
    finally:
        for nome in BACKENDS:
            log = subprocess.run([*DC, "logs", "--no-color", nome], capture_output=True)
            (saida / f"app-{nome}.log").write_bytes(log.stdout + log.stderr)
        dc("up", "-d", "--force-recreate", *BACKENDS)
        dc("restart", "proxy")
        limpar_esquema()


def pytest_gabarito(saida, nome, ids=()):
    alvos = [str(V2 / "gabarito" / i) for i in ids] or [str(V2 / "gabarito")]
    cmd = [sys.executable, "-m", "pytest", *alvos, "-q", "--tb=short", "-p", "no:cacheprovider",
           f"--junitxml={saida / (nome + '.xml')}"]
    return subprocess.run(cmd, cwd=DEMOS, capture_output=True, text=True)


class ProjetoV2(Projeto):
    def __init__(self, raiz, alvo, grupo):
        super().__init__(raiz, alvo)
        self.grupo, self.gates = grupo, 0

    def rodar_pytest(self):
        self.gates += 1
        with candidato(self.raiz, self.saida) as subiu:
            if not subiu:
                # Contra um app fora do ar a suíte só acumula 502 e gasta o teto de tempo da etapa.
                r = subprocess.CompletedProcess([], 1, "", "App não respondeu; nenhum teste foi executado.")
            elif self.grupo == "rework":
                # Executa a cópia do avaliador, não a do workspace: editar testes não muda o gate.
                r = pytest_gabarito(self.saida, f"gate-{self.gates}", VISIVEIS)
            else:
                r = subprocess.run(
                    ["docker", "run", "--rm", "--network", "caronte-piloto-v2_default", "--read-only", "--tmpfs", "/tmp",
                     "--cap-drop=ALL", "--security-opt=no-new-privileges", "-e", "PYTHONDONTWRITEBYTECODE=1",
                     *(a for k, v in GATE_TDD.items() for a in ("-e", f"{k}={v}")),
                     "-v", f"{self.raiz}:/workspace:ro", "--mount", "type=tmpfs,dst=/workspace/_harness",
                     "-w", "/workspace", RUNTIME, "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
                    capture_output=True, text=True)
        saida = r.stdout + "\n" + r.stderr
        logs = "\n".join(p.read_text(errors="replace")[-4000:] for p in sorted(self.saida.glob("app-*.log")))
        (self.saida / f"pytest-{self.gates}.txt").write_text(saida + ("\n" + logs if r.returncode else ""))
        resultado = ResultadoPytest.de_saida(saida, r.returncode == 0)
        # O coder só vê o fim da saída: com o app de pé, o resumo do pytest; fora do ar, o log de subida.
        return resultado if subiu else replace(resultado, saida=saida + "\n" + logs)


def avaliar(raiz, saida=None):
    """Gabarito inteiro depois da geração; nada volta para a sessão."""
    saida = saida or raiz / "_harness"
    with candidato(raiz, saida):
        r = pytest_gabarito(saida, "gabarito")
    (saida / "gabarito.txt").write_text(r.stdout + "\n" + r.stderr)
    casos = {f"{Path(t.get('classname').replace('.', '/')).name}.py::{t.get('name')}":
             t.find("failure") is None and t.find("error") is None
             for t in ET.parse(saida / "gabarito.xml").iter("testcase")}
    resultado = {"passed": sum(casos.values()), "total": len(casos), "runtime_image": RUNTIME,
                 "relatorio": json.loads((ESTADO / "GABARITO.json").read_text())}
    for grupo in ("visiveis", "reservados"):
        selecionados = [casos[i] for i in SPLIT[grupo]]
        resultado[grupo] = {"passed": sum(selecionados), "total": len(selecionados)}
    resultado["fontes_sha256"] = {str(p.relative_to(raiz)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in raiz.rglob("*.py") if "_harness" not in p.relative_to(raiz).parts}
    (saida / "GABARITO.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    return resultado


def definidos(no):
    if isinstance(no, (ast.FunctionDef, ast.ClassDef)):
        return {no.name}
    if isinstance(no, ast.Assign):
        return {t.id for t in no.targets if isinstance(t, ast.Name)}
    return set()


def podar(modulo, importados):
    """Tira dados, fixtures e parametrizações que só os testes reservados usavam."""
    while True:
        usos = [{x.id if isinstance(x, ast.Name) else x.arg for x in ast.walk(n) if isinstance(x, (ast.Name, ast.arg))}
                for n in modulo.body]
        orfaos = [n for i, n in enumerate(modulo.body) if definidos(n) and not any(
            nome.startswith("test_") or nome in ("pytestmark", *importados) or any(nome in u for j, u in enumerate(usos) if j != i)
            for nome in definidos(n))]
        if not orfaos:
            return
        modulo.body = [n for n in modulo.body if n not in orfaos]


def preparar_rework(requisito=REQUISITO, destino=V2 / "entrada-rework"):
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(requisito, destino)
    texto = (destino / "alvo.toml").read_text().replace("../../caronte/skills.lock.json", "../../skills.lock.json")
    (destino / "alvo.toml").write_text(texto)
    (destino / "requisito.md").write_text((V2 / "rework.md").read_text())
    testes = destino / "tests"
    testes.mkdir()
    visiveis = {}
    for i in VISIVEIS:
        arquivo, funcao = i.split("::")
        visiveis.setdefault(arquivo, set()).add(funcao)
    modulos = {}
    for arquivo, funcoes in visiveis.items():
        modulo = ast.parse((V2 / "gabarito" / arquivo).read_text())
        modulo.body = [n for n in modulo.body if not (isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                                                      and n.name not in funcoes)]
        modulos[arquivo] = modulo
    importados = {a.name for m in modulos.values() for n in m.body
                  if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("test_") for a in n.names}
    for arquivo, modulo in modulos.items():
        podar(modulo, importados)
        (testes / arquivo).write_text(ast.unparse(modulo) + "\n")
    for nome in ("conftest.py",):
        shutil.copyfile(V2 / "gabarito" / nome, testes / nome)
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
    parser.add_argument("--saida", type=Path, help="pasta dos resultados, para não sobrescrever _harness")
    args = parser.parse_args()
    if args.grupo == "avaliar":
        r = avaliar(Path(args.projeto).resolve(), args.saida and args.saida.resolve())
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
