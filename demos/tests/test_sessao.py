import asyncio
import json
import re
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from harness.models import sessao as modulo
from harness.models.dominio import Alvo, Projeto
from harness.models.etapas import CODIGO, SO_TESTES
from harness.models.sessao import IMAGEM, VERSAO, Sessao

ALVO = Alvo(comando_app="app", comando_teste="pytest -q", python="3.11", pacotes=())


def test_escopo_vira_regra_de_edicao_do_opencode():
    assert SO_TESTES.permissao == {"*": "deny", "tests/**": "allow"}
    assert CODIGO.permissao["*"] == "allow"
    for negado in ("tests/**", "pytest.ini", "conftest.py", "_harness/**", ".git/**"):
        assert CODIGO.permissao[negado] == "deny"


def test_turno_soma_tokens_custo_e_registra_skills():
    eventos = [
        {"type": "step_start", "sessionID": "ses_1", "part": {}},
        {"type": "tool_use", "sessionID": "ses_1",
         "part": {"tool": "skill", "state": {"input": {"name": "ponytail"}}}},
        {"type": "step_finish", "sessionID": "ses_1", "part": {"cost": 0.004, "tokens": {
            "total": 120, "input": 40, "output": 15, "reasoning": 5,
            "cache": {"read": 60, "write": 0}}}},
    ]
    sessao = Sessao("coder", "z-ai/glm-5.3")

    turno = sessao._turno("\n".join(json.dumps(e) for e in eventos), None)

    assert sessao.id == "ses_1"
    assert (turno.input_tokens, turno.output_tokens, turno.total_tokens) == (100, 20, 120)
    assert turno.custo_usd == 0.004
    assert turno.skills == ["ponytail"] and turno.erro is None


class Provedor(BaseHTTPRequestHandler):
    """OpenRouter falso: grava o corpo de cada chamada ao modelo e responde, em ordem, as
    escritas do roteiro como chamadas de ferramenta; depois, só texto."""

    pedidos: list[dict] = []
    roteiro: list[str | dict] = []

    def do_POST(self):
        Provedor.pedidos.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        if Provedor.roteiro:
            acao = Provedor.roteiro.pop(0)
            ferramenta = acao["tool"] if isinstance(acao, dict) else "write"
            argumentos = json.dumps(acao["input"] if isinstance(acao, dict) else {"filePath": acao, "content": "x = 1\n"})
            delta = {"role": "assistant", "tool_calls": [{
                "index": 0, "id": f"call_{len(Provedor.pedidos)}", "type": "function",
                "function": {"name": ferramenta, "arguments": argumentos}}]}
            fim = "tool_calls"
        else:
            delta, fim = {"role": "assistant", "content": "ok"}, "stop"
        pedaco = {
            "id": "x", "object": "chat.completion.chunk", "created": 0, "model": "m",
            "choices": [{"index": 0, "delta": delta, "finish_reason": fim}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
        }
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(f"data: {json.dumps(pedaco)}\n\ndata: [DONE]\n\n".encode())

    def log_message(self, *args):
        pass


def opencode_fixado() -> bool:
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "image", "inspect", IMAGEM],
                          capture_output=True).returncode == 0


def conversar(monkeypatch, projeto, escopo, skills=(), roteiro=()):
    servidor = ThreadingHTTPServer(("0.0.0.0", 0), Provedor)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    # shortcut: host.docker.internal exige Docker Desktop; usar provedor em container no CI Linux.
    monkeypatch.setattr(modulo, "API", f"http://host.docker.internal:{servidor.server_port}/v1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-falsa")
    Provedor.pedidos, Provedor.roteiro = [], list(roteiro)
    papel = "test_writer" if escopo is SO_TESTES else "coder"
    try:
        sessao = Sessao(papel, "z-ai/glm-5.3")
        return asyncio.run(sessao.enviar("REQUISITO", projeto, escopo.permissao, list(skills), 120))
    finally:
        servidor.shutdown()


@pytest.mark.skipif(not opencode_fixado(), reason=f"requer opencode {VERSAO}")
def test_sessao_nao_leva_ambiente_de_quem_roda(tmp_path, monkeypatch):
    # Projeto dentro de um repositório com instruções, skills e config próprias, como
    # uma run dentro do repositório do TCC.
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "AGENTS.md").write_text("CANARIO-AGENTS")
    (repo / "CLAUDE.md").write_text("CANARIO-CLAUDE")
    vazada = repo / ".claude" / "skills" / "vazada"
    vazada.mkdir(parents=True)
    (vazada / "SKILL.md").write_text("---\nname: vazada\ndescription: Nunca.\n---\nCANARIO-SKILL\n")
    (repo / ".opencode").mkdir()
    (repo / ".opencode" / "opencode.json").write_text('{"instructions": ["AGENTS.md"]}')
    fixa = tmp_path / "skills" / "fixa"
    fixa.mkdir(parents=True)
    (fixa / "SKILL.md").write_text("---\nname: fixa\ndescription: A liberada.\n---\nx\n")
    projeto = Projeto(repo / "demos" / "run", ALVO)
    projeto.preparar()

    turno = conversar(monkeypatch, projeto, CODIGO, [fixa])

    assert turno.erro is None
    # Uma chamada só: --title evita a do título, que ficaria fora da contabilidade.
    assert len(Provedor.pedidos) == 1
    assert Provedor.pedidos[0]["temperature"] == 0.1
    assert Provedor.pedidos[0]["top_p"] == 0.9
    corpo = json.dumps(Provedor.pedidos[0], ensure_ascii=False)
    assert "Instructions from:" not in corpo
    for canario in ("CANARIO-AGENTS", "CANARIO-CLAUDE", "CANARIO-SKILL"):
        assert canario not in corpo
    assert sorted(set(re.findall(r"<name>([^<]+)</name>", corpo))) == ["fixa"]
    assert "Você implementa código de produção" in corpo
    ferramentas = {f["function"]["name"] for f in Provedor.pedidos[0]["tools"]}
    assert "bash" not in ferramentas
    assert turno.custo_usd > 0 and turno.total_tokens == 10
    assert (projeto.saida / "opencode" / "coder-1.jsonl").is_file()


@pytest.mark.skipif(not opencode_fixado(), reason=f"requer opencode {VERSAO}")
@pytest.mark.parametrize("em_repo", [False, True])
@pytest.mark.parametrize(
    "escopo, permitido, negado",
    [(SO_TESTES, "tests/test_x.py", "app.py"), (CODIGO, "app.py", "tests/test_x.py")],
)
def test_escopo_vale_dentro_e_fora_de_repositorio(tmp_path, monkeypatch, em_repo, escopo, permitido, negado):
    # O opencode casa o padrão com o caminho relativo ao topo do git, ou a `/` fora dele.
    pai = tmp_path / "pai"
    pai.mkdir()
    if em_repo:
        subprocess.run(["git", "init", "-q", str(pai)], check=True)
    projeto = Projeto(pai / "runs" / "run", ALVO)
    projeto.preparar()

    conversar(monkeypatch, projeto, escopo, roteiro=[permitido, negado])

    assert (projeto.raiz / permitido).is_file()
    assert not (projeto.raiz / negado).exists()


@pytest.mark.skipif(not opencode_fixado(), reason=f"requer opencode {VERSAO}")
def test_sessao_nao_le_original_ou_oraculo_no_repo_pai(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    original = repo / "original.py"
    original.write_text("CANARIO-ORIGINAL-OCULTO")
    oraculo = repo / "oraculo.py"
    oraculo.write_text("CANARIO-ORACULO-OCULTO")
    fixa = repo / "skills" / "fixa"
    fixa.mkdir(parents=True)
    (fixa / "SKILL.md").write_text("---\nname: fixa\ndescription: A liberada.\n---\nCANARIO-SKILL-PERMITIDA\n")
    projeto = Projeto(repo / "runs" / "run", ALVO)
    projeto.preparar()
    (projeto.raiz / "entrada.txt").write_text("CANARIO-ENTRADA-PERMITIDA")
    (projeto.saida / "segredo.txt").write_text("CANARIO-MEDICAO-OCULTA")
    roteiro = [
        {"tool": "read", "input": {"filePath": "/workspace/entrada.txt"}},
        {"tool": "read", "input": {"filePath": str(original)}},
        {"tool": "read", "input": {"filePath": str(oraculo)}},
        {"tool": "grep", "input": {"path": str(repo), "pattern": "CANARIO"}},
        {"tool": "glob", "input": {"path": str(repo), "pattern": "*.py"}},
        {"tool": "grep", "input": {"path": "/workspace", "pattern": "CANARIO"}},
        {"tool": "skill", "input": {"name": "fixa"}},
    ]

    turno = conversar(monkeypatch, projeto, CODIGO, [fixa], roteiro)

    assert turno.erro is None
    corpo = json.dumps(Provedor.pedidos, ensure_ascii=False)
    assert "CANARIO-ENTRADA-PERMITIDA" in corpo
    assert "CANARIO-SKILL-PERMITIDA" in corpo
    assert "CANARIO-ORIGINAL-OCULTO" not in corpo
    assert "CANARIO-ORACULO-OCULTO" not in corpo
    assert "CANARIO-MEDICAO-OCULTA" not in corpo
