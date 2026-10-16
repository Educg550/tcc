"""Separa a suíte em 75% visíveis e 25% reservados, estratificados por rota; grava split.json.

Regra: total reservado = round(N * 0,25); cada rota recebe floor(n * 0,25) e as vagas restantes vão
pelo maior resto, sem reservar todos os testes de uma rota; empate vai para a rota maior e depois
para a de menor nome. Dentro da rota, reserva os testes de menor sha256 do id.

uso (de demos/): uv run python caronte/oraculo/split.py
"""

import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROTA = {
    "test_api_responde": "/",
    "test_login_local_reconhece_o_docente": "/auth/login",
    "test_lista_o_edital": "/edicts",
    "test_consulta_o_edital": "/edicts/1",
    "test_encontra_a_inscricao_pelo_nome": "/edicts/1/submissions",
    "test_consultas_repetidas_nao_duplicam": "/edicts/1/submissions",
    "test_detalhe_identifica_a_candidata": "/submissions/1",
    "test_detalhe_traz_as_respostas_da_secao": "/submissions/1",
    "test_baixa_o_anexo": "/submissions/1/files",
}


def rota(nodeid):
    nome, param = re.match(r".*::(\w+)(?:\[(.*)\])?$", nodeid).groups()
    return param if nome == "test_sem_atalho_e_sem_sessao_responde_401" else ROTA[nome]


def vagas(tamanhos, fracao=0.25):
    base = {r: math.floor(n * fracao) for r, n in tamanhos.items()}
    sobra = round(sum(tamanhos.values()) * fracao) - sum(base.values())
    candidatas = sorted((r for r, n in tamanhos.items() if base[r] < n - 1),
                        key=lambda r: (-(tamanhos[r] * fracao - base[r]), -tamanhos[r], r))
    for r in candidatas[:sobra]:
        base[r] += 1
    return base


def test_vagas_maior_resto():
    tamanhos = {"/": 1, "/auth/login": 2, "/edicts": 2, "/edicts/1": 1,
                "/edicts/1/submissions": 3, "/submissions/1": 10, "/submissions/1/files": 8}
    assert vagas(tamanhos) == {"/": 0, "/auth/login": 1, "/edicts": 0, "/edicts/1": 0,
                               "/edicts/1/submissions": 1, "/submissions/1": 3, "/submissions/1/files": 2}


if __name__ == "__main__":
    saida = subprocess.run(["uv", "run", "pytest", "--collect-only", "-q", str(AQUI / "test_consulta.py")],
                           capture_output=True, text=True, check=True).stdout
    ids = [l for l in saida.splitlines() if "::" in l]
    por_rota = {}
    for i in ids:
        por_rota.setdefault(rota(i), []).append(i)
    reservados = []
    for r, k in vagas({r: len(v) for r, v in por_rota.items()}).items():
        reservados += sorted(por_rota[r], key=lambda i: hashlib.sha256(i.encode()).hexdigest())[:k]
    split = {"regra": __doc__.split("\n\n")[1], "visiveis": sorted(set(ids) - set(reservados)),
             "reservados": sorted(reservados)}
    (AQUI / "split.json").write_text(json.dumps(split, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(split['visiveis'])} visíveis, {len(reservados)} reservados")
