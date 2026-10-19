"""Infraestrutura isolada do v2. Uso: python caronte/piloto-v2/ambiente.py preparar."""
import argparse
import io
import json
import re
import subprocess
import tarfile
import time
from pathlib import Path

import httpx

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
DADOS = AQUI / "dados"
ESTADO = AQUI / ".estado"
URL = "https://localhost:8543"
DC = ["docker", "compose", "-f", str(AQUI / "compose.yml")]


def dc(*args, entrada=None, check=True):
    resultado = subprocess.run([*DC, *args], input=entrada, text=True,
                               capture_output=True)
    if check and resultado.returncode:
        raise RuntimeError(resultado.stderr or resultado.stdout)
    return resultado


def sql(consulta, banco="prejanus", usuario=None):
    return dc("exec", "-T", "db", "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1",
              "-U", usuario or "caronte_admin", "-d", f"caronte_{banco}",
              entrada=consulta).stdout.strip()


def linhas(consulta, banco="prejanus"):
    return json.loads(sql(f"SELECT coalesce(json_agg(q), '[]') FROM ({consulta}) q;", banco))


def esperar(url, tentativas=60):
    for _ in range(tentativas):
        try:
            if httpx.get(url, verify=False, timeout=2).status_code < 500:
                return
        except httpx.HTTPError:
            pass
        time.sleep(.5)
    raise RuntimeError(f"Serviço não respondeu: {url}")


def pdf(texto):
    objetos = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
               "/Resources << /Font << /F1 5 0 R >> >> >>",
               f"<< /Length {len(texto) + 25} >>\nstream\nBT /F1 12 Tf 72 720 Td ({texto}) Tj ET\nendstream",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    corpo, posicoes = b"%PDF-1.4\n", []
    for i, o in enumerate(objetos, 1):
        posicoes.append(len(corpo))
        corpo += f"{i} 0 obj\n{o}\nendobj\n".encode()
    xref = "".join(f"{p:010d} 00000 n \n" for p in posicoes)
    return corpo + (f"xref\n0 6\n0000000000 65535 f \n{xref}trailer\n<< /Size 6 /Root 1 0 R >>\n"
                    f"startxref\n{len(corpo)}\n%%EOF\n").encode()


def anexos():
    return linhas("SELECT r.response_id, f.name, r.value FROM responses r JOIN form_field f "
                  "ON f.id = r.field_id WHERE f.type = 'File' AND r.value <> '' ORDER BY 1, 2", "forms")


def limpar_esquema():
    """Apaga tabelas que um candidato criou fora do esquema original, antes do próximo."""
    for banco in ("forms", "prejanus"):
        texto = (RAIZ / f"demos/requisitos/03-caronte-prejanus-completo/infra/esquema-{banco}.sql").read_text()
        originais = set(re.findall(r'CREATE TABLE public\."?(\w+)', texto))
        extras = [t["tablename"] for t in linhas("SELECT tablename FROM pg_tables WHERE schemaname='public'", banco)
                  if t["tablename"] not in originais]
        if extras:
            sql("DROP TABLE " + ", ".join(f'"{t}"' for t in extras) + " CASCADE;", banco)


def restaurar():
    # Só o projeto Compose fixo deste módulo: nunca usa os bancos/containers do v1.
    for banco in ("forms", "prejanus"):
        tabelas = linhas("SELECT tablename FROM pg_tables WHERE schemaname='public' "
                         "AND tablename NOT IN ('alembic_version','migrations')", banco)
        nomes = ", ".join('"' + t["tablename"] + '"' for t in tabelas)
        sql(f"BEGIN; TRUNCATE {nomes} RESTART IDENTITY CASCADE;\n"
            + (DADOS / f"{banco}.sql").read_text() + "\nCOMMIT;", banco)
    dc("exec", "-T", "redis", "redis-cli", "FLUSHDB")
    pacote = io.BytesIO()
    with tarfile.open(fileobj=pacote, mode="w") as tar:
        for a in anexos():
            dado = pdf(f"Piloto v2 - resposta {a['response_id']} - {a['name']}")
            info = tarfile.TarInfo(a["value"])
            info.size = len(dado)
            tar.addfile(info, io.BytesIO(dado))
    subprocess.run([*DC, "exec", "-T", "-u", "0", "forms", "sh", "-c",
                    "rm -rf /shared/uploads/* && tar x -o -C /shared/uploads"],
                   input=pacote.getvalue(), check=True, capture_output=True)


def preparar():
    ESTADO.mkdir(exist_ok=True)
    tls = ESTADO / "tls"
    tls.mkdir(exist_ok=True)
    if not (tls / "cert.pem").exists():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", str(tls / "key.pem"), "-out", str(tls / "cert.pem"),
                        "-days", "3650", "-subj", "/CN=localhost", "-addext",
                        "subjectAltName=DNS:localhost,IP:127.0.0.1"],
                       check=True, capture_output=True)
    dc("up", "-d", "--wait", "db", "redis", "smtp", "oauth")
    origem = RAIZ / "demos/requisitos/02-caronte-consulta/infra"
    existentes = linhas("SELECT tablename FROM pg_tables WHERE schemaname='public'", "forms")
    if not existentes:
        for banco in ("forms", "prejanus"):
            # Dono do esquema é o usuário da aplicação, para valerem os grants padrão do init original.
            esquema = (origem / f"esquema-{banco}.sql").read_text().replace("COMMENT ON EXTENSION", "-- ")
            sql(esquema, banco, f"caronte_{banco}")
        sql((origem / "fixture-forms.sql").read_text(), "forms", "caronte_forms")
        sql("INSERT INTO users(email,role,created_at) VALUES "
            "('admin.piloto@example.com','administrator',now());", "forms")
        for comando in ("create_doctorate_application_form doutorado 2026",
                        "create_accept_form mestrado 2026"):
            dc("run", "--rm", "--no-deps", "--entrypoint", "flask", "forms",
               "commands", *comando.split())
    if not (DADOS / "forms.sql").exists():
        if linhas("SELECT id FROM submission") or linhas("SELECT id FROM form_response", "forms"):
            raise RuntimeError("Carga incompleta com respostas existentes; preservar estado e investigar.")
        dc("up", "-d", "prejanus-back")
        fixtures = {"FIXTURE_PREJANUS": "fixture-prejanus.sql",
                    "FIXTURE_CONSULTA": "fixture-consulta-forms.sql",
                    "FIXTURE_INSCRICAO": "fixture-consulta-prejanus.sql"}
        texto = "\n".join(f"{nome} = {(origem / arquivo).read_text()!r}"
                          for nome, arquivo in fixtures.items())
        texto = 'FIXTURE_USUARIOS = ' + (origem / "seed.sql").read_text().__repr__() + '\n' + texto
        dc("exec", "-T", "prejanus-back", "python",
           entrada=texto + "\n" + (AQUI / "semear.py").read_text())
        for banco in ("forms", "prejanus"):
            dump = dc("exec", "-T", "db", "pg_dump", "--data-only", "--column-inserts",
                      "--no-owner", "--no-privileges", "--exclude-table-data=alembic_version",
                      "-U", "caronte_admin",
                      f"caronte_{banco}").stdout
            # Não restaurar o controle de migrações como parte dos dados de um cenário.
            (DADOS / f"{banco}.sql").write_text(dump)
    dc("up", "-d", "prejanus-back", "local", "sem-atalho", "forms", "worker", "front", "proxy")
    for caminho in ("/backend/", "/local/", "/sem-atalho/", "/prejanus/login", "/pt/"):
        esperar(URL + caminho)
    restaurar()
    imagens = json.loads(dc("images", "--format", "json").stdout)
    (ESTADO / "imagens.json").write_text(json.dumps(imagens, indent=2) + "\n")
    print(f"Ambiente v2: {URL}; SMTP http://localhost:8182; bancos e rede próprios.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("acao", choices=("preparar", "restaurar", "parar"))
    acao = parser.parse_args().acao
    if acao == "preparar":
        preparar()
    elif acao == "restaurar":
        restaurar()
    else:
        dc("stop")
