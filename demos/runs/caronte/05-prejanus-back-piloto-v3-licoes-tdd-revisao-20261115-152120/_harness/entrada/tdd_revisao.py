"""Variante exploratória: o coder pode revisar os testes autorais, com histórico."""

import difflib
import json
from pathlib import Path

from harness.models.etapas import CODIGO, SO_TESTES, Escopo, EtapaTDD
from harness.models.harness import HarnessTDD


class EscopoRevisao(Escopo):
    def validar(self, raiz: Path, caminho: str, conteudo: str) -> Path:
        destino = self.destino(raiz, caminho)
        escopo = SO_TESTES if destino.is_relative_to(raiz / "tests") else CODIGO
        return escopo.validar(raiz, caminho, conteudo)


class EtapaTDDRevisao(EtapaTDD):
    escopo = EscopoRevisao(fora=tuple(p for p in CODIGO.fora if p != "tests"))

    def registrar_testes(self, projeto):
        atuais = {str(p.relative_to(projeto.raiz)): p.read_text(encoding="utf-8")
                  for p in sorted((projeto.raiz / "tests").rglob("*"))
                  if p.is_file() and not {"__pycache__", ".pytest_cache"} & set(p.parts)}
        if atuais == self.anteriores:
            return
        numero = len(self.versoes)
        pasta = projeto.saida / "revisoes-testes"
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"{numero:03}.json").write_text(
            json.dumps(atuais, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        antes = self.anteriores or {}
        alterados = sorted(n for n in antes.keys() | atuais.keys() if antes.get(n) != atuais.get(n))
        if numero:
            diff = "".join(linha for nome in alterados for linha in difflib.unified_diff(
                antes.get(nome, "").splitlines(keepends=True),
                atuais.get(nome, "").splitlines(keepends=True),
                fromfile=f"antes/{nome}", tofile=f"depois/{nome}",
            ))
            (pasta / f"{numero:03}.diff").write_text(diff, encoding="utf-8")
        registro = {"versao": numero, "sha256": projeto.impressao(), "arquivos": alterados}
        self.versoes.append(registro)
        self.trace.registrar({"evento": "versao_testes", **registro})
        self.anteriores = atuais

    async def executar(self, base, projeto):
        self.anteriores, self.versoes = None, []
        self.registrar_testes(projeto)
        try:
            parte = await super().executar(base, projeto)
        finally:
            # Uma sessão interrompida pode gravar testes e sair antes do gate.
            self.registrar_testes(projeto)
        return {**parte, "testes_revisaveis": True, "versoes_testes": self.versoes}

    def verificar(self, projeto):
        self.registrar_testes(projeto)
        return super().verificar(projeto)


class HarnessTDDRevisao(HarnessTDD):
    grupo = "tdd-revisao"

    def agente(self, papel, model_id, classe):
        return super().agente("coder_revisao" if papel == "coder" else papel, model_id, classe)

    def etapa(self, id, agente, classe):
        return super().etapa(id, agente, EtapaTDDRevisao if classe is EtapaTDD else classe)
