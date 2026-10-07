import json
import random
import secrets
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file

GALERIA = Path("runs/galeria").resolve()
ESTADO = GALERIA / "torneio.json"
TELAS = ("1-alunos.png", "2-docentes.png", "3-oficio.png")


def mata_mata(vivos, escolhas, partidas):
    """Fora de potência de 2, só as primeiras 2·(n − p) jogam e o resto passa direto."""
    while len(vivos) > 1:
        n, p = len(vivos), 1 << (len(vivos).bit_length() - 1)
        jogam = n if n == p else 2 * (n - p)
        vencedoras = []
        for a, b in zip(vivos[:jogam:2], vivos[1:jogam:2]):
            if len(partidas) == len(escolhas):
                return None, (a, b)
            vencedora = escolhas[len(partidas)]
            partidas.append((a, b, vencedora))
            vencedoras.append(vencedora)
        vivos = vencedoras + vivos[jogam:]
    return vivos[0], None


def torneio(ordem, escolhas):
    """A 2ª melhor só pode ter perdido para a campeã: a repescagem entre essas acha a vice."""
    partidas = []
    campea, par = mata_mata(ordem, escolhas, partidas)
    if par:
        return par, len(partidas), "chave", None
    perdedoras = [b if v == a else a for a, b, v in partidas if v == campea]
    vice, par = mata_mata(perdedoras, escolhas, partidas)
    return par, len(partidas), "repescagem", None if par else (campea, vice)


app = Flask(__name__)
estado = {}


def situacao():
    ordem = sorted(estado["candidatos"])
    random.Random(estado["seed"]).shuffle(ordem)
    par, n, fase, fim = torneio(ordem, estado["escolhas"])
    if par and random.Random(f'{estado["seed"]}-{n}').random() < 0.5:
        par = par[::-1]
    return par, n, fase, fim


def salvar():
    fim = situacao()[3]
    estado["resultado"] = fim and dict(zip(("campea", "vice"), (estado["candidatos"][t] for t in fim)))
    ESTADO.write_text(json.dumps(estado, indent=1, ensure_ascii=False))


@app.get("/")
def pagina():
    return send_file(Path(__file__).with_name("index.html"))


@app.get("/estado")
def ver():
    par, n, fase, _ = situacao()
    return jsonify(par=par, partida=n + 1, fase=fase, resultado=estado["resultado"])


@app.get("/img/<token>/<int:n>")
def imagem(token, n):
    if token not in estado["candidatos"] or n not in (1, 2, 3):
        abort(404)
    return send_file(GALERIA / estado["candidatos"][token] / TELAS[n - 1])


@app.post("/escolha")
def escolher():
    par = situacao()[0]
    if not par or request.json["vencedor"] not in par:
        abort(409)
    estado["escolhas"].append(request.json["vencedor"])
    salvar()
    return ver()


@app.post("/desfazer")
def desfazer():
    if estado["escolhas"]:
        estado["escolhas"].pop()
        salvar()
    return ver()


if __name__ == "__main__":
    if ESTADO.exists():
        estado.update(json.loads(ESTADO.read_text()))
    else:
        pastas = sorted(p.name for p in GALERIA.iterdir() if all((p / t).is_file() for t in TELAS))
        estado.update(seed=secrets.randbits(32), escolhas=[],
                      candidatos={secrets.token_hex(4): p for p in pastas})
    salvar()
    print(f'{len(estado["candidatos"])} candidatas')
    app.run(port=8090)
