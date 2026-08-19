from pathlib import Path

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
