import random

from desempatador.__main__ import torneio


def test_repescagem_acha_a_verdadeira_vice():
    for seed in range(20):
        ordem = [f"r{i}" for i in range(81)]
        random.Random(seed).shuffle(ordem)
        escolhas = []
        while par := torneio(ordem, escolhas)[0]:
            escolhas.append(min(par, key=lambda r: int(r[1:])))
        _, partidas, _, fim = torneio(ordem, escolhas)
        assert fim == ("r0", "r1")
        assert partidas in (85, 86)
