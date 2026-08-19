import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .agents import MODEL_TESTS, make_coder, make_test_writer
from .loop import Orcamento, como_mudanca, escrever, loop_tdd, rodar_pytest

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

EXTENSOES = (".py", ".html", ".css", ".js")


def modo(projeto: Path) -> str:
    """Não existe flag de modo: quem decide é o estado do diretório."""
    projeto = Path(projeto)
    if not projeto.exists() or not any(projeto.iterdir()):
        return "criacao"
    return "manutencao"


def contexto(projeto: Path) -> str:
    """Código e testes atuais, para o test-writer em modo manutenção.

    ponytail: despeja o projeto inteiro no prompt. Teto conhecido: quando não couber
    na janela, virar leitura seletiva. Para o tamanho do caso do IME, cabe.
    """
    projeto = Path(projeto)
    partes = []
    for caminho in sorted(projeto.rglob("*")):
        if not caminho.is_file() or caminho.suffix not in EXTENSOES:
            continue
        rel = caminho.relative_to(projeto)
        if any(parte.startswith(".") for parte in rel.parts):
            continue
        partes.append(f"### {rel}\n```\n{caminho.read_text(encoding='utf-8')}\n```")
    return "\n\n".join(partes)


def build_run_log(
    *, started_at, ended_at, total_duration_s, modo, requisito_id, stages, loop,
    pytest_final, regressao, cua,
) -> dict:
    # O loop entra na soma: o custo do coder é a maior fatia da execução.
    partes = stages + [loop] + ([cua] if cua else [])
    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "total_duration_s": total_duration_s,
        "modo": modo,
        "requisito_id": requisito_id,
        "total_cost_usd": sum((p.get("cost_usd") or 0.0) for p in partes) or None,
        "total_tokens": sum((p.get("total_tokens") or 0) for p in partes) or None,
        "total_retries": sum(p.get("retries", 0) for p in partes),
        "stages": stages,
        "loop": loop,
        "pytest_final": pytest_final,
        "regressao": regressao,
        "cua": cua,
    }


def aprovar(label: str, conteudo: str, yes: bool) -> str | None:
    """Gate humano. None quando aprovado, senão o texto do feedback.

    Com yes=True não pergunta nada: é o modo batch do experimento, onde os dois
    grupos precisam receber exatamente a mesma ajuda humana, ou seja, nenhuma.
    """
    if yes:
        return None
    barra = "═" * 60
    print(f"\n{barra}\n  Etapa: {label}\n{barra}\n{conteudo}\n{barra}")
    while True:
        r = input(f"[{label}] aprovar? (y/n): ").strip().lower()
        if r == "y":
            return None
        if r == "n":
            break
        print("  Digite 'y' ou 'n'.")
    feedback = ""
    while not feedback.strip():
        feedback = input("Feedback: ")
    return feedback.strip()


def _metricas(resposta) -> dict:
    m = getattr(resposta, "metrics", None)
    return {
        "input_tokens": getattr(m, "input_tokens", None),
        "output_tokens": getattr(m, "output_tokens", None),
        "total_tokens": getattr(m, "total_tokens", None),
        "cost_usd": getattr(m, "cost", None),
    }


async def stage_tests(projeto: Path, requisito: str, modo_atual: str, yes: bool) -> dict:
    agente = make_test_writer()
    base = requisito
    if modo_atual == "manutencao":
        base += "\n\n## PROJETO ATUAL\n\n" + contexto(projeto)

    feedback, retries = None, 0
    while True:
        prompt = base if feedback is None else f"{base}\n\n## FEEDBACK ANTERIOR\n{feedback}\n"
        inicio = time.time()
        resposta = await agente.arun(prompt)
        escritos = escrever(como_mudanca(resposta.content), projeto, escopo="tests")
        metricas = _metricas(resposta)
        feedback = aprovar("tests", "\n".join(escritos), yes)
        if feedback is None:
            return {
                "id": "tests",
                "configured_model": MODEL_TESTS,
                "duration_s": round(time.time() - inicio, 2),
                "retries": retries,
                "arquivos": escritos,
                **metricas,
            }
        retries += 1


async def stage_code(projeto: Path, requisito: str, saida: Path, yes: bool) -> dict:
    agente = make_coder()
    base = (
        f"{requisito}\n\n## TESTES A FAZER PASSAR\n\n"
        f"{contexto(projeto / 'tests')}\n"
    )
    feedback, retries = None, 0
    while True:
        prompt = base if feedback is None else f"{base}\n\n## FEEDBACK ANTERIOR\n{feedback}\n"
        resultado = await loop_tdd(
            agente, prompt, projeto, Orcamento(), saida / "trace.jsonl"
        )
        feedback = aprovar(
            "code", f"{resultado['motivo']} em {resultado['passos']} passos", yes
        )
        if feedback is None:
            return {**resultado, "retries": retries}
        retries += 1


def commitar(projeto: Path, requisito_id: str) -> None:
    """Um commit por requisito no projeto gerado: dá diff, tamanho e rollback."""
    if not (projeto / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=projeto, check=True)
    subprocess.run(["git", "add", "-A"], cwd=projeto, check=True)
    subprocess.run(["git", "commit", "-q", "-m", requisito_id], cwd=projeto, check=False)


async def executar(projeto: Path, requisito: Path, yes: bool) -> dict:
    projeto, requisito = Path(projeto), Path(requisito)
    modo_atual = modo(projeto)
    projeto.mkdir(parents=True, exist_ok=True)
    saida = projeto / "_harness"
    saida.mkdir(exist_ok=True)

    texto = (requisito / "requisito.md").read_text(encoding="utf-8")
    inicio, started_at = time.time(), datetime.now().isoformat(timespec="seconds")

    antes = rodar_pytest(projeto) if modo_atual == "manutencao" else None
    tests = await stage_tests(projeto, texto, modo_atual, yes)
    vermelho = not rodar_pytest(projeto).passou
    code = await stage_code(projeto, texto, saida, yes)
    final = rodar_pytest(projeto)
    commitar(projeto, requisito.name)

    log = build_run_log(
        started_at=started_at,
        ended_at=datetime.now().isoformat(timespec="seconds"),
        total_duration_s=round(time.time() - inicio, 2),
        modo=modo_atual,
        requisito_id=requisito.name,
        stages=[tests],
        loop={**code, "tests_vermelhos": vermelho},
        pytest_final={
            "passed": final.passed,
            "failed": final.failed,
            "errors": final.errors,
            "total": final.total,
        },
        regressao=(
            None
            if antes is None
            else {
                "antes": {"passed": antes.passed, "failed": antes.failed},
                "depois": {"passed": final.passed, "failed": final.failed},
                "quebrou": antes.failed == 0 and final.failed > 0,
            }
        ),
        cua=None,
    )
    (saida / "RUN.log").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return log
