"""Materializa em skills/ cada skill do skills.lock.json, no commit fixado, conferindo a
árvore git e o SHA-256 do SKILL.md contra o manifesto."""

import hashlib
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI / "skills"

ATRIBUICAO = """# Atribuição

Cópia sem modificações de `{path}` em {repository}, commit `{commit}`.

O repositório não tem arquivo LICENSE nessa revisão. A licença {license} é a declarada
nos arquivos abaixo, no mesmo commit; os de fora da skill estão copiados em `_origem/`:

{evidencias}
"""


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def vendorizar(skill: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        git(repo, "init", "-q")
        git(repo, "fetch", "-q", "--depth", "1", "--filter=blob:none", skill["repository"], skill["commit"])
        arvore = git(repo, "rev-parse", f"FETCH_HEAD:{skill['path']}").decode().strip()
        assert arvore == skill["tree_git_sha"], f"{skill['name']}: árvore {arvore}"

        alvo = DESTINO / skill["name"]
        shutil.rmtree(alvo, ignore_errors=True)
        tar = git(repo, "archive", "--format=tar", f"FETCH_HEAD:{skill['path']}")
        with tarfile.open(fileobj=io.BytesIO(tar)) as t:
            t.extractall(alvo, filter="data")
        sha = hashlib.sha256((alvo / "SKILL.md").read_bytes()).hexdigest()
        assert sha == skill["skill_sha256"], f"{skill['name']}: SKILL.md {sha}"

        for evidencia in skill["license_evidence"]:
            dentro = Path(evidencia["path"]).is_relative_to(skill["path"])
            # Evidência de dentro da skill já veio no archive; copiá-la para _origem/ duplicaria um SKILL.md.
            copia = alvo / (Path(evidencia["path"]).relative_to(skill["path"]) if dentro else Path("_origem") / evidencia["path"])
            if not dentro:
                copia.parent.mkdir(parents=True, exist_ok=True)
                copia.write_bytes(git(repo, "show", f"FETCH_HEAD:{evidencia['path']}"))
            assert hashlib.sha256(copia.read_bytes()).hexdigest() == evidencia["sha256"], copia

    if skill["license_evidence_type"] == "declaration_only":
        evidencias = "\n".join(f"- [{e['path']}]({e['url']})" for e in skill["license_evidence"])
        (alvo / "ATTRIBUTION.md").write_text(ATRIBUICAO.format(evidencias=evidencias, **skill), encoding="utf-8")


if __name__ == "__main__":
    for skill in json.loads((AQUI / "skills.lock.json").read_text())["skills"]:
        vendorizar(skill)
        print("ok", skill["name"])
