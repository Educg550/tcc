import base64
import json
import os
import shutil
import time

from browser_use import Agent as AgenteNavegador
from browser_use import ChatOpenAI
from pydantic import BaseModel

from .agentes import Agente, load
from .dominio import MEDIDO, Criterio, Projeto, Requisito
from .etapas import Escopo

# Teto de passos por critério. O default do browser-use é 500, que numa sessão empacada
# vira consumo sem fim; baixo demais viraria falso negativo, porque a sessão termina sem
# veredito e o critério conta como reprovado.
MAX_PASSOS_CUA = 80
# O default do browser-use e 4096: o CUA trunca a acao no meio do JSON, o passo vira erro
# de validacao e o criterio e reprovado por falha do avaliador, nao do app.
MAX_TOKENS_CUA = 16000
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# A suíte vive dentro da medição: fora do contexto que o modelo recebe, e já proibida ao
# coder pelo escopo que ele tem.
SPECS = Escopo(dentro="_harness/cypress/e2e")


class VeredictoCriterio(BaseModel):
    """Uma sessão julga um critério só, então não há id: quem sabe qual é é o harness."""

    passou: bool
    evidencia: str


def resumir(criterios: list[dict]) -> str:
    """Derivado das partes, não pedido a um modelo: nenhuma sessão vê o conjunto."""
    return "\n".join(
        f"{c['identificador']} passou"
        if c["passou"]
        else f"{c['identificador']} FALHOU: {c['evidencia']}"
        for c in criterios
    )


def _veredito(criterio: Criterio, blobs: list[dict]) -> dict:
    """Casa o critério com os testes pelo título do `describe`, que é o identificador.
    Comparação exata no primeiro termo, e não `startswith`: `C1` casaria com `C14`."""

    def e_dele(t: dict) -> bool:
        return t["fullTitle"].split(" ", 1)[0] == criterio.identificador

    testes = [t for b in blobs for t in b["tests"] if e_dele(t)]
    falhas = [f for b in blobs for f in b["failures"] if e_dele(f)]
    aprovados = [t for b in blobs for t in b["passes"] if e_dele(t)]
    pendentes = [t for b in blobs for t in b["pending"] if e_dele(t)]
    passou = bool(testes) and not falhas and not pendentes and len(aprovados) == len(testes)
    return {
        "identificador": criterio.identificador,
        "passou": passou,
        "evidencia": "; ".join(f["err"]["message"] for f in falhas)
        # Critério sem spec nenhum é reprovação do avaliador, e precisa aparecer como tal
        # em vez de passar por omissão.
        or (f"testes aprovados: {len(testes)}" if passou else
            "há testes que não passaram" if testes else "nenhum spec para o critério"),
        "num_testes": len(testes),
    }


class Avaliador:
    """A avaliação final, sobre o app rodando e depois do código, igual nos dois grupos.

    Dois instrumentos: o Cypress julga o que é verificável sem julgamento, e é
    determinístico e repetível; o CUA julga o que sobra - aparência, proporção, o que só
    se decide olhando. O CUA continua sendo caixa-preta, só deixou de ser o único."""

    def __init__(self, model_id: str, model_specs: str):
        self.model_id = model_id
        self.model_specs = model_specs

    async def _cypress(self, projeto: Projeto, requisito: Requisito) -> dict:
        """Escreve a suíte a partir dos critérios e roda. O agente vê o código - nos dois
        grupos o app já existe quando ele roda -, mas o que ele afirma vem do critério."""
        inicio = time.time()
        criterios = requisito.deterministicos
        if not criterios:
            return {}
        if not projeto.alvo.comando_frontend:
            return {
                "aprovado": False,
                "criterios": [
                    {**_veredito(c, []), "evidencia": "teste_frontend não configurado"}
                    for c in criterios
                ],
            }

        agente = Agente(
            self.model_specs, load("cypress_writer") + "\n\n" + load("cypress_regras")
        )
        prompt = "\n\n".join(
            [
                "## CRITÉRIOS\n\n"
                + "\n\n".join(
                    f"### {c.identificador}\n\nAção:\n{c.acao}\n\n"
                    f"Resultado esperado:\n{c.resultado_esperado}"
                    for c in criterios
                ),
                "## CÓDIGO DA APLICAÇÃO\n\n" + projeto.contexto(".", fora=MEDIDO),
            ]
        )
        resposta = await agente.propor(prompt)
        if resposta.mudanca is None:
            arquivos, blobs, saida = [], [], f"o modelo não devolveu Mudanca: {resposta.erro}"
        else:
            # Suíte anterior fora: reavaliar o mesmo projeto com nomes de arquivo
            # diferentes deixaria os specs velhos rodando junto com os novos.
            shutil.rmtree(projeto.saida / "cypress" / "e2e", ignore_errors=True)
            proposta = SPECS.aplicar(resposta.mudanca, projeto)
            arquivos = getattr(proposta, "arquivos", [])
            blobs, saida = projeto.rodar_frontend()

        vereditos = [_veredito(c, blobs) for c in criterios]
        return {
            "configured_model": self.model_specs,
            "duration_s": round(time.time() - inicio, 2),
            "cost_usd": round(resposta.custo_usd, 6),
            "total_tokens": resposta.total_tokens,
            "arquivos": arquivos,
            # O stdout só interessa quando nenhum spec rodou: é onde está o motivo.
            "saida": "" if blobs else saida[-4000:],
            "aprovado": all(v["passou"] for v in vereditos),
            "criterios": vereditos,
        }

    @staticmethod
    def _tela(projeto: Projeto, criterio: str, history) -> str | None:
        """A última tela que o CUA viu: a evidência de onde o veredito saiu."""
        b64 = next((t for t in reversed(history.screenshots(n_last=3)) if t), None)
        if not b64:
            return None
        destino = projeto.saida / f"{criterio}.png"
        destino.write_bytes(base64.b64decode(b64))
        return destino.name

    async def _sessao(self, projeto: Projeto, url: str, criterio: Criterio) -> dict:
        agente = AgenteNavegador(
            task=load("cua_task").format(
                base_url=url,
                acao=criterio.acao,
                resultado_esperado=criterio.resultado_esperado,
            ),
            llm=ChatOpenAI(
                model=self.model_id,
                base_url=OPENROUTER_BASE,
                api_key=os.environ["OPENROUTER_API_KEY"],
                max_completion_tokens=MAX_TOKENS_CUA,
            ),
            output_model_schema=VeredictoCriterio,
            generate_gif=False,
            calculate_cost=True,
        )
        history = await agente.run(max_steps=MAX_PASSOS_CUA)
        v, usage = history.structured_output, history.usage
        return {
            "identificador": criterio.identificador,
            "passou": v.passou if v else False,
            "evidencia": v.evidencia if v else "sessão terminou sem veredito",
            "tela": self._tela(projeto, criterio.identificador, history),
            "duration_s": round(history.total_duration_seconds() or 0.0, 2),
            "num_steps": history.number_of_steps(),
            "cost_usd": usage.total_cost if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
        }

    async def _cua(self, projeto: Projeto, requisito: Requisito) -> dict:
        """Uma sessão limpa por critério, em série e com o app subido de novo: o app
        guarda estado em memória, e reaproveitar o processo traz o critério anterior de
        volta para dentro do seguinte."""
        inicio = time.time()
        criterios = []
        for criterio in requisito.subjetivos:
            with projeto.rodando(f"-{criterio.identificador}") as url:
                criterios.append(await self._sessao(projeto, url, criterio))
        return {
            "configured_model": self.model_id,
            "duration_s": round(time.time() - inicio, 2),
            "num_steps": sum(c["num_steps"] or 0 for c in criterios),
            "cost_usd": round(sum(c["cost_usd"] or 0.0 for c in criterios), 6),
            "total_tokens": sum(c["total_tokens"] or 0 for c in criterios),
            "aprovado": all(c["passou"] for c in criterios),
            "criterios": criterios,
        }

    async def avaliar(self, projeto: Projeto, requisito: Requisito) -> dict:
        """Os dois instrumentos, e o veredito sobre o conjunto. Grava o AVALIACAO.log
        próprio: a avaliação mede o app, não o pipeline que o fez."""
        cypress = await self._cypress(projeto, requisito)
        cua = await self._cua(projeto, requisito)

        todos = cypress.get("criterios", []) + cua["criterios"]
        resultado = {
            "aprovado_geral": all(c["passou"] for c in todos),
            "cost_usd": round(cypress.get("cost_usd", 0.0) + cua["cost_usd"], 6),
            "resumo": resumir(todos),
            "cypress": cypress,
            "cua": cua,
        }
        (projeto.saida / "AVALIACAO.log").write_text(
            json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return resultado
