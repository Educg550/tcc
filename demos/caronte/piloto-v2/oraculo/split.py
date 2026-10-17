"""Separa a suíte v2 em 75% visíveis e 25% reservados; grava split.json.

Regra: a unidade é a função de teste, com todas as suas parametrizações. Estratos são o primeiro
requisito da função. Total reservado = round(N * 0,25) funções; cada estrato recebe floor(n * 0,25) e as
vagas restantes vão pelo maior resto, sem reservar todas as funções de um estrato; empate vai para o
estrato maior e depois para o de menor nome. Dentro do estrato, reserva as funções de menor sha256 do
nome do arquivo e da função. test_rastreio fica fora da partição.

uso (de demos/): uv run python caronte/piloto-v2/oraculo/split.py
"""

import hashlib
import json
import math
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent


def vagas(tamanhos, fracao=0.25):
    base = {r: math.floor(n * fracao) for r, n in tamanhos.items()}
    sobra = round(sum(tamanhos.values()) * fracao) - sum(base.values())
    candidatas = sorted((r for r, n in tamanhos.items() if base[r] < n - 1),
                        key=lambda r: (-(tamanhos[r] * fracao - base[r]), -tamanhos[r], r))
    for r in candidatas[:sobra]:
        base[r] += 1
    return base


def test_vagas_maior_resto():
    assert vagas({"A": 4, "B": 2, "C": 1, "D": 3}) == {"A": 1, "B": 0, "C": 0, "D": 1}


class Coletor:
    funcoes = {}

    def pytest_collection_modifyitems(self, items):
        for item in items:
            arquivo, funcao = item.nodeid.split("oraculo/")[-1].split("[")[0].split("::")
            if arquivo != "test_rastreio.py":
                req = next(item.iter_markers("req")).args[0]
                self.funcoes.setdefault(f"{arquivo}::{funcao}", (req, []))[1].append(item.nodeid.split("oraculo/")[-1])


if __name__ == "__main__":
    assert pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", str(AQUI)], plugins=[Coletor()]) == 0
    por_req = {}
    for funcao, (req, _) in Coletor.funcoes.items():
        por_req.setdefault(req, []).append(funcao)
    reservadas = []
    for req, k in vagas({r: len(f) for r, f in por_req.items()}).items():
        reservadas += sorted(por_req[req], key=lambda f: hashlib.sha256(f.encode()).hexdigest())[:k]
    casos = lambda fs: sorted(c for f in fs for c in Coletor.funcoes[f][1])
    split = {"regra": __doc__.split("\n\n")[1], "reservadas": sorted(reservadas),
             "visiveis": casos(set(Coletor.funcoes) - set(reservadas)), "reservados": casos(reservadas)}
    (AQUI / "split.json").write_text(json.dumps(split, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(Coletor.funcoes) - len(reservadas)} funções visíveis, {len(reservadas)} reservadas; "
          f"{len(split['visiveis'])} casos visíveis, {len(split['reservados'])} reservados")
