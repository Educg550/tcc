"""
Testes de aceitacao para a CLI `task`.

Invoca o modulo via `python -m task ...` usando subprocess.run, isolando
cada teste com tmp_path para garantir que tasks.json nao vaze entre testes.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(args: list[str], cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess:
    """Executa `python -m task <args>` no diretorio cwd."""
    cmd = [sys.executable, "-m", "task"] + args
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        input=input_text,
    )


def load_tasks(cwd: Path) -> dict:
    """Le tasks.json do diretorio cwd e retorna o dict parsed."""
    return json.loads((cwd / "tasks.json").read_text())


# ---------------------------------------------------------------------------
# Criacao do tasks.json na primeira execucao
# ---------------------------------------------------------------------------

class TestFirstUse:
    def test_tasks_json_criado_automaticamente(self, tmp_path):
        """Se tasks.json nao existe, o primeiro comando deve cria-lo."""
        assert not (tmp_path / "tasks.json").exists()
        run(["add", "Primeira tarefa"], cwd=tmp_path)
        assert (tmp_path / "tasks.json").exists()

    def test_estrutura_inicial_do_json(self, tmp_path):
        """tasks.json criado deve ter version=1 e lista tasks."""
        run(["add", "Tarefa inicial"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["version"] == 1
        assert isinstance(data["tasks"], list)

    def test_list_sem_tasks_json_nao_falha(self, tmp_path):
        """list em diretorio sem tasks.json nao deve lancar erro."""
        result = run(["list"], cwd=tmp_path)
        assert result.returncode == 0

    def test_tasks_json_criado_pelo_list(self, tmp_path):
        """list deve criar tasks.json se nao existir."""
        run(["list"], cwd=tmp_path)
        assert (tmp_path / "tasks.json").exists()


# ---------------------------------------------------------------------------
# Comando add
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_simples(self, tmp_path):
        result = run(["add", "Minha tarefa"], cwd=tmp_path)
        assert result.returncode == 0

    def test_add_persiste_titulo(self, tmp_path):
        run(["add", "Tarefa persistida"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert any(t["title"] == "Tarefa persistida" for t in data["tasks"])

    def test_add_id_auto_incremental(self, tmp_path):
        run(["add", "Tarefa 1"], cwd=tmp_path)
        run(["add", "Tarefa 2"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        ids = [t["id"] for t in data["tasks"]]
        assert ids == [1, 2]

    def test_add_prioridade_default_low(self, tmp_path):
        run(["add", "Sem prioridade explicita"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "low"

    def test_add_prioridade_high(self, tmp_path):
        run(["add", "Urgente", "-p", "high"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "high"

    def test_add_prioridade_medium(self, tmp_path):
        run(["add", "Media", "-p", "medium"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "medium"

    def test_add_prioridade_low_explicita(self, tmp_path):
        run(["add", "Baixa", "-p", "low"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "low"

    def test_add_prioridade_invalida_retorna_erro(self, tmp_path):
        result = run(["add", "Titulo", "-p", "urgent"], cwd=tmp_path)
        assert result.returncode != 0

    def test_add_prioridade_invalida_nao_cria_tarefa(self, tmp_path):
        run(["add", "Titulo", "-p", "urgent"], cwd=tmp_path)
        if (tmp_path / "tasks.json").exists():
            data = load_tasks(tmp_path)
            assert len(data["tasks"]) == 0

    def test_add_com_data_valida(self, tmp_path):
        run(["add", "Com vencimento", "-d", "2025-12-31"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["due_date"] == "2025-12-31"

    def test_add_sem_data_due_date_null(self, tmp_path):
        run(["add", "Sem vencimento"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["due_date"] is None

    def test_add_data_malformada_retorna_erro(self, tmp_path):
        result = run(["add", "Data invalida", "-d", "31-12-2025"], cwd=tmp_path)
        assert result.returncode != 0

    def test_add_data_inexistente_retorna_erro(self, tmp_path):
        """Datas como 2025-02-30 sao invalidas."""
        result = run(["add", "Data imposivel", "-d", "2025-02-30"], cwd=tmp_path)
        assert result.returncode != 0

    def test_add_done_inicial_false(self, tmp_path):
        run(["add", "Nova tarefa"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["done"] is False

    def test_add_created_at_presente(self, tmp_path):
        run(["add", "Com timestamp"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["created_at"] != ""
        assert data["tasks"][0]["created_at"] is not None

    def test_add_saida_contem_id(self, tmp_path):
        result = run(["add", "Com ID na saida"], cwd=tmp_path)
        assert "1" in result.stdout

    def test_add_flags_longas_prioridade(self, tmp_path):
        run(["add", "Flag longa", "--priority", "high"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "high"

    def test_add_flags_longas_data(self, tmp_path):
        run(["add", "Flag longa data", "--due", "2025-06-15"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["due_date"] == "2025-06-15"

    def test_add_multiplas_tarefas_ids_unicos(self, tmp_path):
        for i in range(5):
            run(["add", f"Tarefa {i}"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        ids = [t["id"] for t in data["tasks"]]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Comando list
# ---------------------------------------------------------------------------

class TestList:
    def test_list_vazio_sem_erro(self, tmp_path):
        result = run(["list"], cwd=tmp_path)
        assert result.returncode == 0

    def test_list_mostra_tarefa_pendente(self, tmp_path):
        run(["add", "Tarefa pendente"], cwd=tmp_path)
        result = run(["list"], cwd=tmp_path)
        assert "Tarefa pendente" in result.stdout

    def test_list_oculta_tarefas_concluidas_por_padrao(self, tmp_path):
        run(["add", "Concluida"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        result = run(["list"], cwd=tmp_path)
        assert "Concluida" not in result.stdout

    def test_list_all_inclui_concluidas(self, tmp_path):
        run(["add", "Concluida"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        result = run(["list", "-a"], cwd=tmp_path)
        assert "Concluida" in result.stdout

    def test_list_all_flag_longa(self, tmp_path):
        run(["add", "Concluida"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        result = run(["list", "--all"], cwd=tmp_path)
        assert "Concluida" in result.stdout

    def test_list_done_apenas_concluidas(self, tmp_path):
        run(["add", "Pendente"], cwd=tmp_path)
        run(["add", "Concluida"], cwd=tmp_path)
        run(["done", "2"], cwd=tmp_path)
        result = run(["list", "--done"], cwd=tmp_path)
        assert "Concluida" in result.stdout
        assert "Pendente" not in result.stdout

    def test_list_filtra_por_prioridade_high(self, tmp_path):
        run(["add", "Alta", "-p", "high"], cwd=tmp_path)
        run(["add", "Baixa", "-p", "low"], cwd=tmp_path)
        result = run(["list", "-p", "high"], cwd=tmp_path)
        assert "Alta" in result.stdout
        assert "Baixa" not in result.stdout

    def test_list_filtra_por_prioridade_medium(self, tmp_path):
        run(["add", "Alta", "-p", "high"], cwd=tmp_path)
        run(["add", "Media", "-p", "medium"], cwd=tmp_path)
        result = run(["list", "-p", "medium"], cwd=tmp_path)
        assert "Media" in result.stdout
        assert "Alta" not in result.stdout

    def test_list_filtra_por_prioridade_low(self, tmp_path):
        run(["add", "Alta", "-p", "high"], cwd=tmp_path)
        run(["add", "Baixa", "-p", "low"], cwd=tmp_path)
        result = run(["list", "-p", "low"], cwd=tmp_path)
        assert "Baixa" in result.stdout
        assert "Alta" not in result.stdout

    def test_list_retorno_zero(self, tmp_path):
        run(["add", "Qualquer"], cwd=tmp_path)
        result = run(["list"], cwd=tmp_path)
        assert result.returncode == 0

    def test_list_exibe_prioridade(self, tmp_path):
        run(["add", "Alta prioridade", "-p", "high"], cwd=tmp_path)
        result = run(["list"], cwd=tmp_path)
        assert "high" in result.stdout

    def test_list_exibe_data_vencimento(self, tmp_path):
        run(["add", "Com data", "-d", "2025-11-01"], cwd=tmp_path)
        result = run(["list"], cwd=tmp_path)
        assert "2025-11-01" in result.stdout

    def test_list_exibe_id(self, tmp_path):
        run(["add", "Tarefa com id"], cwd=tmp_path)
        result = run(["list"], cwd=tmp_path)
        assert "1" in result.stdout


# ---------------------------------------------------------------------------
# Comando done
# ---------------------------------------------------------------------------

class TestDone:
    def test_done_marca_concluida(self, tmp_path):
        run(["add", "Para concluir"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["done"] is True

    def test_done_retorno_zero(self, tmp_path):
        run(["add", "Para concluir"], cwd=tmp_path)
        result = run(["done", "1"], cwd=tmp_path)
        assert result.returncode == 0

    def test_done_id_inexistente_retorna_erro(self, tmp_path):
        run(["add", "Unica tarefa"], cwd=tmp_path)
        result = run(["done", "999"], cwd=tmp_path)
        assert result.returncode != 0

    def test_done_id_inexistente_mensagem_erro(self, tmp_path):
        run(["add", "Unica tarefa"], cwd=tmp_path)
        result = run(["done", "999"], cwd=tmp_path)
        output = result.stdout + result.stderr
        assert "999" in output or "nao encontrada" in output.lower() or "not found" in output.lower() or "inexistente" in output.lower() or "invalid" in output.lower()

    def test_done_sem_tarefas_id_inexistente(self, tmp_path):
        """done em lista vazia deve retornar erro."""
        result = run(["done", "1"], cwd=tmp_path)
        assert result.returncode != 0

    def test_done_nao_altera_outros_campos(self, tmp_path):
        run(["add", "Titulo original", "-p", "high", "-d", "2025-09-01"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        t = data["tasks"][0]
        assert t["title"] == "Titulo original"
        assert t["priority"] == "high"
        assert t["due_date"] == "2025-09-01"

    def test_done_nao_altera_outras_tarefas(self, tmp_path):
        run(["add", "Tarefa 1"], cwd=tmp_path)
        run(["add", "Tarefa 2"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        t2 = next(t for t in data["tasks"] if t["id"] == 2)
        assert t2["done"] is False


# ---------------------------------------------------------------------------
# Comando edit
# ---------------------------------------------------------------------------

class TestEdit:
    def test_edit_titulo(self, tmp_path):
        run(["add", "Titulo antigo"], cwd=tmp_path)
        run(["edit", "1", "--title", "Titulo novo"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["title"] == "Titulo novo"

    def test_edit_prioridade(self, tmp_path):
        run(["add", "Tarefa", "-p", "low"], cwd=tmp_path)
        run(["edit", "1", "-p", "high"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "high"

    def test_edit_data(self, tmp_path):
        run(["add", "Tarefa", "-d", "2025-01-01"], cwd=tmp_path)
        run(["edit", "1", "-d", "2025-12-31"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["due_date"] == "2025-12-31"

    def test_edit_retorno_zero(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["edit", "1", "--title", "Novo"], cwd=tmp_path)
        assert result.returncode == 0

    def test_edit_id_inexistente_retorna_erro(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["edit", "999", "--title", "Novo"], cwd=tmp_path)
        assert result.returncode != 0

    def test_edit_prioridade_invalida_retorna_erro(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["edit", "1", "-p", "critical"], cwd=tmp_path)
        assert result.returncode != 0

    def test_edit_data_malformada_retorna_erro(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["edit", "1", "-d", "2025/12/31"], cwd=tmp_path)
        assert result.returncode != 0

    def test_edit_nao_altera_campos_nao_passados(self, tmp_path):
        run(["add", "Titulo", "-p", "high", "-d", "2025-06-01"], cwd=tmp_path)
        run(["edit", "1", "--title", "Novo titulo"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        t = data["tasks"][0]
        assert t["priority"] == "high"
        assert t["due_date"] == "2025-06-01"

    def test_edit_multiplos_campos_simultaneos(self, tmp_path):
        run(["add", "Antigo", "-p", "low"], cwd=tmp_path)
        run(["edit", "1", "--title", "Novo", "-p", "medium", "-d", "2025-08-15"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        t = data["tasks"][0]
        assert t["title"] == "Novo"
        assert t["priority"] == "medium"
        assert t["due_date"] == "2025-08-15"

    def test_edit_nao_altera_outras_tarefas(self, tmp_path):
        run(["add", "Tarefa 1"], cwd=tmp_path)
        run(["add", "Tarefa 2"], cwd=tmp_path)
        run(["edit", "1", "--title", "Editada"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        t2 = next(t for t in data["tasks"] if t["id"] == 2)
        assert t2["title"] == "Tarefa 2"

    def test_edit_data_invalida_nao_altera_tarefa(self, tmp_path):
        run(["add", "Tarefa", "-d", "2025-03-10"], cwd=tmp_path)
        run(["edit", "1", "-d", "nao-e-data"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["due_date"] == "2025-03-10"

    def test_edit_flag_longa_prioridade(self, tmp_path):
        run(["add", "Tarefa", "-p", "low"], cwd=tmp_path)
        run(["edit", "1", "--priority", "high"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["priority"] == "high"

    def test_edit_flag_longa_data(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        run(["edit", "1", "--due", "2025-10-20"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["due_date"] == "2025-10-20"


# ---------------------------------------------------------------------------
# Comando delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_com_force_remove_tarefa(self, tmp_path):
        run(["add", "Para deletar"], cwd=tmp_path)
        run(["delete", "1", "--force"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert not any(t["id"] == 1 for t in data["tasks"])

    def test_delete_com_force_retorno_zero(self, tmp_path):
        run(["add", "Para deletar"], cwd=tmp_path)
        result = run(["delete", "1", "--force"], cwd=tmp_path)
        assert result.returncode == 0

    def test_delete_id_inexistente_retorna_erro(self, tmp_path):
        run(["add", "Unica"], cwd=tmp_path)
        result = run(["delete", "999", "--force"], cwd=tmp_path)
        assert result.returncode != 0

    def test_delete_sem_force_pede_confirmacao(self, tmp_path):
        run(["add", "Para deletar"], cwd=tmp_path)
        result = run(["delete", "1"], cwd=tmp_path, input_text="n\n")
        output = result.stdout + result.stderr
        # deve exibir algum prompt de confirmacao
        assert "y" in output.lower() or "confirm" in output.lower() or "?" in output or "n" in output.lower()

    def test_delete_sem_force_confirma_com_y(self, tmp_path):
        run(["add", "Para deletar"], cwd=tmp_path)
        run(["delete", "1"], cwd=tmp_path, input_text="y\n")
        data = load_tasks(tmp_path)
        assert not any(t["id"] == 1 for t in data["tasks"])

    def test_delete_sem_force_cancela_com_n(self, tmp_path):
        run(["add", "Nao deletar"], cwd=tmp_path)
        run(["delete", "1"], cwd=tmp_path, input_text="n\n")
        data = load_tasks(tmp_path)
        assert any(t["id"] == 1 for t in data["tasks"])

    def test_delete_sem_force_cancela_sem_input(self, tmp_path):
        """Enter vazio (default N) deve cancelar a delecao."""
        run(["add", "Nao deletar"], cwd=tmp_path)
        run(["delete", "1"], cwd=tmp_path, input_text="\n")
        data = load_tasks(tmp_path)
        assert any(t["id"] == 1 for t in data["tasks"])

    def test_delete_nao_remove_outras_tarefas(self, tmp_path):
        run(["add", "Tarefa 1"], cwd=tmp_path)
        run(["add", "Tarefa 2"], cwd=tmp_path)
        run(["delete", "1", "--force"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert any(t["id"] == 2 for t in data["tasks"])

    def test_delete_todos_e_adiciona_novo_id_unico(self, tmp_path):
        """Apos deletar tudo, novo add nao deve reusar ID deletado ou pode -- contanto que seja unico."""
        run(["add", "Tarefa 1"], cwd=tmp_path)
        run(["delete", "1", "--force"], cwd=tmp_path)
        run(["add", "Tarefa nova"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Tarefa nova"


# ---------------------------------------------------------------------------
# Comando show
# ---------------------------------------------------------------------------

class TestShow:
    def test_show_exibe_titulo(self, tmp_path):
        run(["add", "Tarefa detalhada"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        assert "Tarefa detalhada" in result.stdout

    def test_show_exibe_prioridade(self, tmp_path):
        run(["add", "Tarefa", "-p", "high"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        assert "high" in result.stdout

    def test_show_exibe_data_vencimento(self, tmp_path):
        run(["add", "Tarefa", "-d", "2025-07-04"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        assert "2025-07-04" in result.stdout

    def test_show_exibe_status_done(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        output = result.stdout.lower()
        assert "done" in output or "concluida" in output or "true" in output or "sim" in output

    def test_show_exibe_created_at(self, tmp_path):
        run(["add", "Tarefa com data de criacao"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        # created_at deve estar em formato ISO 8601 (contem T ou espaco entre data e hora)
        assert result.returncode == 0
        # pelo menos o ano deve aparecer
        import datetime
        year = str(datetime.datetime.now().year)
        assert year in result.stdout

    def test_show_retorno_zero(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        assert result.returncode == 0

    def test_show_id_inexistente_retorna_erro(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["show", "999"], cwd=tmp_path)
        assert result.returncode != 0

    def test_show_id_inexistente_mensagem(self, tmp_path):
        run(["add", "Tarefa"], cwd=tmp_path)
        result = run(["show", "999"], cwd=tmp_path)
        output = result.stdout + result.stderr
        assert "999" in output or len(output.strip()) > 0

    def test_show_sem_tarefas_id_inexistente(self, tmp_path):
        result = run(["show", "1"], cwd=tmp_path)
        assert result.returncode != 0

    def test_show_exibe_id(self, tmp_path):
        run(["add", "Tarefa com id"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        assert "1" in result.stdout

    def test_show_tarefa_correta_entre_varias(self, tmp_path):
        run(["add", "Primeira"], cwd=tmp_path)
        run(["add", "Segunda"], cwd=tmp_path)
        run(["add", "Terceira"], cwd=tmp_path)
        result = run(["show", "2"], cwd=tmp_path)
        assert "Segunda" in result.stdout
        assert "Primeira" not in result.stdout
        assert "Terceira" not in result.stdout


# ---------------------------------------------------------------------------
# Edge cases e integracao entre comandos
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_id_string_invalido_retorna_erro(self, tmp_path):
        """IDs nao numericos devem falhar."""
        result = run(["done", "abc"], cwd=tmp_path)
        assert result.returncode != 0

    def test_add_titulo_com_espacos(self, tmp_path):
        run(["add", "Titulo com espacos e mais palavras"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert data["tasks"][0]["title"] == "Titulo com espacos e mais palavras"

    def test_sequencia_add_done_list(self, tmp_path):
        """Fluxo completo: adiciona, conclui, verifica list."""
        run(["add", "Fluxo completo"], cwd=tmp_path)
        run(["done", "1"], cwd=tmp_path)
        result_padrao = run(["list"], cwd=tmp_path)
        result_all = run(["list", "-a"], cwd=tmp_path)
        assert "Fluxo completo" not in result_padrao.stdout
        assert "Fluxo completo" in result_all.stdout

    def test_sequencia_add_edit_show(self, tmp_path):
        """Edita e verifica com show."""
        run(["add", "Original", "-p", "low"], cwd=tmp_path)
        run(["edit", "1", "--title", "Editado", "-p", "high"], cwd=tmp_path)
        result = run(["show", "1"], cwd=tmp_path)
        assert "Editado" in result.stdout
        assert "high" in result.stdout

    def test_sequencia_add_delete_add_show(self, tmp_path):
        """Deleta e adiciona nova tarefa."""
        run(["add", "Primeira"], cwd=tmp_path)
        run(["delete", "1", "--force"], cwd=tmp_path)
        run(["add", "Segunda"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Segunda"

    def test_persistencia_entre_chamadas(self, tmp_path):
        """Verifica que tasks.json e realmente persistido entre processos diferentes."""
        run(["add", "Persistida 1"], cwd=tmp_path)
        run(["add", "Persistida 2"], cwd=tmp_path)
        data = load_tasks(tmp_path)
        assert len(data["tasks"]) == 2

    def test_tasks_json_no_cwd_nao_em_home(self, tmp_path):
        """tasks.json deve ser criado no cwd, nao em ~/."""
        home_tasks = Path.home() / "tasks.json"
        existia_antes = home_tasks.exists()
        run(["add", "Tarefa local"], cwd=tmp_path)
        assert (tmp_path / "tasks.json").exists()
        if not existia_antes:
            assert not home_tasks.exists()

    def test_data_formato_incorreto_letras(self, tmp_path):
        result = run(["add", "Titulo", "-d", "amanha"], cwd=tmp_path)
        assert result.returncode != 0

    def test_data_formato_mes_invalido(self, tmp_path):
        result = run(["add", "Titulo", "-d", "2025-13-01"], cwd=tmp_path)
        assert result.returncode != 0

    def test_prioridade_case_sensitive(self, tmp_path):
        """HIGH em maiusculas deve falhar (enum e lower case)."""
        result = run(["add", "Titulo", "-p", "HIGH"], cwd=tmp_path)
        assert result.returncode != 0

    def test_list_all_e_done_juntos_nao_mistura(self, tmp_path):
        """--done filtra apenas concluidas mesmo com multiplas tarefas."""
        run(["add", "Pendente 1"], cwd=tmp_path)
        run(["add", "Pendente 2"], cwd=tmp_path)
        run(["add", "Concluida"], cwd=tmp_path)
        run(["done", "3"], cwd=tmp_path)
        result = run(["list", "--done"], cwd=tmp_path)
        assert "Concluida" in result.stdout
        assert "Pendente 1" not in result.stdout
        assert "Pendente 2" not in result.stdout

    def test_list_filtro_prioridade_sem_resultados(self, tmp_path):
        """list -p high quando nao ha tarefas high deve ter saida vazia ou retorno 0."""
        run(["add", "So low", "-p", "low"], cwd=tmp_path)
        result = run(["list", "-p", "high"], cwd=tmp_path)
        assert result.returncode == 0
        assert "So low" not in result.stdout
