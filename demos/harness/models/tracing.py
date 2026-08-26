import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Trace:
    """Uma linha JSON por passo do modelo."""

    caminho: Path

    def registrar(self, evento: dict) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.caminho.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")


@dataclass
class Resultado:
    """O RUN.log: a unidade de medida do TCC, não log de depuração. Os totais são
    derivados das partes, nunca passados a mão."""

    modo: str
    requisito_id: str
    alvo: dict | None = None
    orcamento: dict | None = None
    antes: dict | None = None
    stages: list[dict] = field(default_factory=list)
    loop: dict | None = None
    pytest_final: dict | None = None
    impressao: str | None = None
    impressao_fim: str | None = None
    cua: dict | None = None
    comeco: datetime = field(default_factory=datetime.now)

    @property
    def partes(self) -> list[dict]:
        return [*self.stages, *(p for p in (self.loop, self.cua) if p)]

    @property
    def regressao(self) -> dict | None:
        if self.antes is None or self.pytest_final is None:
            return None
        return {
            "antes": self.antes,
            "depois": self.pytest_final,
            "quebrou": self.antes["failed"] == 0 and self.pytest_final["failed"] > 0,
        }

    @property
    def integridade(self) -> dict | None:
        """Se `intacto`, os testes que o pytest_final mediu são idênticos aos que
        a etapa de testes gerou. Sem isso o sucesso é afirmação do próprio agente."""
        if self.impressao is None:
            return None
        return {
            "medido_sha256": self.impressao,
            "intacto": self.impressao == self.impressao_fim,
        }

    def como_dict(self) -> dict:
        fim = datetime.now()
        return {
            "started_at": self.comeco.isoformat(timespec="seconds"),
            "ended_at": fim.isoformat(timespec="seconds"),
            "total_duration_s": round((fim - self.comeco).total_seconds(), 2),
            "modo": self.modo,
            "requisito_id": self.requisito_id,
            "alvo": self.alvo,
            "orcamento": self.orcamento,
            "total_cost_usd": round(
                sum(p.get("cost_usd") or 0.0 for p in self.partes), 6
            ),
            "total_tokens": sum(p.get("total_tokens") or 0 for p in self.partes),
            "total_retries": sum(p.get("retries") or 0 for p in self.partes),
            "stages": self.stages,
            "loop": self.loop,
            "pytest_final": self.pytest_final,
            "regressao": self.regressao,
            "integridade": self.integridade,
            "cua": self.cua,
        }

    def gravar(self, caminho: Path) -> dict:
        log = self.como_dict()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(
            json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return log
