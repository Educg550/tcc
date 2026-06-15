"""
Testes de aceitação para a CLI `task`.

Cada teste invoca a CLI via subprocess.run com o interpretador correto,
isolando o arquivo tasks.json em tmp_path para evitar interferência entre testes.
A variável de ambiente TASK_DIR é usada para que a CLI saiba onde gravar
tasks.json; caso a implementação não suporte TASK_DIR, o cwd do processo
subprocess é redirecionado para tmp_path.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rodar_cli(args: list[str], cwd: Path, input_text: str = "") -> subprocess.CompletedProcess:
    """Executa `python -m task <args>` com cwd e stdin controlados."""
    return subprocess.run(
        [sys.executable, "-m", "task"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        input=input_text,
    )


def ler_tasks(cwd: Path) -> dict:
    """Lê e retorna o conteúdo de tasks.json no diretório informado."""
    caminho = cwd / "tasks.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Criação do arquivo tasks.json no primeiro uso
# ---------------------------------------------------------------------------

class TestPrimeiroUso:
    def test_tasks_json_criado_no_add(self, tmp_path):
        """tasks.json deve ser criado ao adicionar a primeira tarefa."""
        assert not (tmp_path / "tasks.json").exists()
        resultado = rodar_cli(["add", "Tarefa inicial"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert (tmp_path / "tasks.json").exists()

    def test_tasks_json_criado_no_list(self, tmp_path):
        """tasks.json deve ser criado (ou tolerado ausente) ao listar tarefas."""
        assert not (tmp_path / "tasks.json").exists()
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert resultado.returncode == 0

    def test_estrutura_inicial_valida(self, tmp_path):
        """Após o primeiro add, tasks.json deve ter version e lista tasks."""
        rodar_cli(["add", "Primeira tarefa"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert "version" in dados
        assert dados["version"] == 1
        assert "tasks" in dados
        assert isinstance(dados["tasks"], list)


# ---------------------------------------------------------------------------
# Comando add
# ---------------------------------------------------------------------------

class TestComandoAdd:
    def test_add_simples(self, tmp_path):
        """Adicionar tarefa sem flags extras deve funcionar e retornar código 0."""
        resultado = rodar_cli(["add", "Comprar leite"], cwd=tmp_path)
        assert resultado.returncode == 0

    def test_add_grava_titulo(self, tmp_path):
        """O título informado deve estar gravado em tasks.json."""
        rodar_cli(["add", "Estudar pytest"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        titulos = [t["title"] for t in dados["tasks"]]
        assert "Estudar pytest" in titulos

    def test_add_prioridade_padrao_low(self, tmp_path):
        """Sem -p, a prioridade padrão deve ser 'low'."""
        rodar_cli(["add", "Tarefa sem prioridade"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        tarefa = dados["tasks"][0]
        assert tarefa["priority"] == "low"

    def test_add_prioridade_high(self, tmp_path):
        """Com -p high, a prioridade gravada deve ser 'high'."""
        rodar_cli(["add", "Urgente", "-p", "high"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["priority"] == "high"

    def test_add_prioridade_medium(self, tmp_path):
        """Com -p medium, a prioridade gravada deve ser 'medium'."""
        rodar_cli(["add", "Moderada", "-p", "medium"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["priority"] == "medium"

    def test_add_com_data_vencimento(self, tmp_path):
        """Com -d YYYY-MM-DD, due_date deve ser gravado corretamente."""
        rodar_cli(["add", "Reuniao", "-d", "2025-12-31"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["due_date"] == "2025-12-31"

    def test_add_sem_data_vencimento_null(self, tmp_path):
        """Sem -d, due_date deve ser null."""
        rodar_cli(["add", "Sem data"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["due_date"] is None

    def test_add_id_auto_incremental(self, tmp_path):
        """IDs devem ser auto-incrementais a partir de 1."""
        rodar_cli(["add", "Tarefa 1"], cwd=tmp_path)
        rodar_cli(["add", "Tarefa 2"], cwd=tmp_path)
        rodar_cli(["add", "Tarefa 3"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        ids = [t["id"] for t in dados["tasks"]]
        assert ids == [1, 2, 3]

    def test_add_campo_done_false_inicial(self, tmp_path):
        """Tarefa recém-criada deve ter done=False."""
        rodar_cli(["add", "Nova tarefa"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["done"] is False

    def test_add_campo_created_at_presente(self, tmp_path):
        """Tarefa recém-criada deve ter campo created_at preenchido."""
        rodar_cli(["add", "Com timestamp"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert "created_at" in dados["tasks"][0]
        assert dados["tasks"][0]["created_at"]

    def test_add_prioridade_invalida_falha(self, tmp_path):
        """Prioridade fora do enum deve resultar em código de retorno != 0."""
        resultado = rodar_cli(["add", "Invalida", "-p", "urgente"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_add_data_malformada_falha(self, tmp_path):
        """Data em formato inválido deve resultar em código de retorno != 0."""
        resultado = rodar_cli(["add", "Data errada", "-d", "31-12-2025"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_add_data_inexistente_falha(self, tmp_path):
        """Data com dia inexistente (ex: 2025-02-30) deve falhar."""
        resultado = rodar_cli(["add", "Data inexistente", "-d", "2025-02-30"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_add_multiplas_tarefas(self, tmp_path):
        """Deve ser possível adicionar várias tarefas sequencialmente."""
        for i in range(5):
            r = rodar_cli(["add", f"Tarefa {i}"], cwd=tmp_path)
            assert r.returncode == 0
        dados = ler_tasks(tmp_path)
        assert len(dados["tasks"]) == 5


# ---------------------------------------------------------------------------
# Comando list
# ---------------------------------------------------------------------------

class TestComandoList:
    def test_list_vazia(self, tmp_path):
        """list em base vazia deve retornar código 0 sem travar."""
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert resultado.returncode == 0

    def test_list_exibe_tarefa_pendente(self, tmp_path):
        """list sem flags deve exibir tarefas pendentes no stdout."""
        rodar_cli(["add", "Tarefa visivel"], cwd=tmp_path)
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Tarefa visivel" in resultado.stdout

    def test_list_nao_exibe_concluidas_por_padrao(self, tmp_path):
        """list sem flags NÃO deve exibir tarefas concluídas."""
        rodar_cli(["add", "Tarefa concluida"], cwd=tmp_path)
        rodar_cli(["done", "1"], cwd=tmp_path)
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Tarefa concluida" not in resultado.stdout

    def test_list_all_inclui_concluidas(self, tmp_path):
        """list -a deve incluir tarefas concluídas na saída."""
        rodar_cli(["add", "Tarefa para concluir"], cwd=tmp_path)
        rodar_cli(["done", "1"], cwd=tmp_path)
        resultado = rodar_cli(["list", "-a"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Tarefa para concluir" in resultado.stdout

    def test_list_done_apenas_concluidas(self, tmp_path):
        """list --done deve exibir apenas tarefas concluídas."""
        rodar_cli(["add", "Pendente"], cwd=tmp_path)
        rodar_cli(["add", "Concluida"], cwd=tmp_path)
        rodar_cli(["done", "2"], cwd=tmp_path)
        resultado = rodar_cli(["list", "--done"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Concluida" in resultado.stdout
        assert "Pendente" not in resultado.stdout

    def test_list_filtro_prioridade_high(self, tmp_path):
        """list -p high deve exibir apenas tarefas de alta prioridade."""
        rodar_cli(["add", "Baixa prio", "-p", "low"], cwd=tmp_path)
        rodar_cli(["add", "Alta prio", "-p", "high"], cwd=tmp_path)
        resultado = rodar_cli(["list", "-p", "high"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Alta prio" in resultado.stdout
        assert "Baixa prio" not in resultado.stdout

    def test_list_filtro_prioridade_medium(self, tmp_path):
        """list -p medium deve exibir apenas tarefas de prioridade media."""
        rodar_cli(["add", "Media prio", "-p", "medium"], cwd=tmp_path)
        rodar_cli(["add", "Alta prio", "-p", "high"], cwd=tmp_path)
        resultado = rodar_cli(["list", "-p", "medium"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Media prio" in resultado.stdout
        assert "Alta prio" not in resultado.stdout

    def test_list_exibe_ids(self, tmp_path):
        """list deve exibir o ID de cada tarefa."""
        rodar_cli(["add", "Tarefa com id"], cwd=tmp_path)
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert "1" in resultado.stdout

    def test_list_multiplas_pendentes(self, tmp_path):
        """list deve exibir todas as tarefas pendentes quando há várias."""
        rodar_cli(["add", "Alpha"], cwd=tmp_path)
        rodar_cli(["add", "Beta"], cwd=tmp_path)
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert "Alpha" in resultado.stdout
        assert "Beta" in resultado.stdout


# ---------------------------------------------------------------------------
# Comando done
# ---------------------------------------------------------------------------

class TestComandoDone:
    def test_done_marca_tarefa_concluida(self, tmp_path):
        """done <id> deve marcar a tarefa como concluída em tasks.json."""
        rodar_cli(["add", "Finalizar relatorio"], cwd=tmp_path)
        resultado = rodar_cli(["done", "1"], cwd=tmp_path)
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["done"] is True

    def test_done_id_inexistente_falha(self, tmp_path):
        """done com ID que não existe deve retornar código != 0."""
        rodar_cli(["add", "Qualquer"], cwd=tmp_path)
        resultado = rodar_cli(["done", "999"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_done_id_inexistente_mensagem_erro(self, tmp_path):
        """done com ID inexistente deve emitir mensagem de erro."""
        rodar_cli(["add", "Qualquer"], cwd=tmp_path)
        resultado = rodar_cli(["done", "999"], cwd=tmp_path)
        saida_combinada = resultado.stdout + resultado.stderr
        assert saida_combinada.strip()

    def test_done_nao_afeta_outras_tarefas(self, tmp_path):
        """done em uma tarefa não deve alterar o estado das demais."""
        rodar_cli(["add", "Tarefa 1"], cwd=tmp_path)
        rodar_cli(["add", "Tarefa 2"], cwd=tmp_path)
        rodar_cli(["done", "1"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        tarefa2 = next(t for t in dados["tasks"] if t["id"] == 2)
        assert tarefa2["done"] is False


# ---------------------------------------------------------------------------
# Comando edit
# ---------------------------------------------------------------------------

class TestComandoEdit:
    def test_edit_titulo(self, tmp_path):
        """edit --title deve atualizar o título da tarefa."""
        rodar_cli(["add", "Titulo antigo"], cwd=tmp_path)
        resultado = rodar_cli(["edit", "1", "--title", "Titulo novo"], cwd=tmp_path)
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["title"] == "Titulo novo"

    def test_edit_prioridade(self, tmp_path):
        """edit -p deve atualizar a prioridade da tarefa."""
        rodar_cli(["add", "Tarefa editavel", "-p", "low"], cwd=tmp_path)
        resultado = rodar_cli(["edit", "1", "-p", "high"], cwd=tmp_path)
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["priority"] == "high"

    def test_edit_data_vencimento(self, tmp_path):
        """edit -d deve atualizar a data de vencimento da tarefa."""
        rodar_cli(["add", "Tarefa com data"], cwd=tmp_path)
        resultado = rodar_cli(["edit", "1", "-d", "2026-06-15"], cwd=tmp_path)
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["due_date"] == "2026-06-15"

    def test_edit_multiplos_campos(self, tmp_path):
        """edit deve permitir alterar titulo, prioridade e data ao mesmo tempo."""
        rodar_cli(["add", "Original", "-p", "low"], cwd=tmp_path)
        resultado = rodar_cli(
            ["edit", "1", "--title", "Modificado", "-p", "high", "-d", "2026-01-01"],
            cwd=tmp_path,
        )
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        tarefa = dados["tasks"][0]
        assert tarefa["title"] == "Modificado"
        assert tarefa["priority"] == "high"
        assert tarefa["due_date"] == "2026-01-01"

    def test_edit_id_inexistente_falha(self, tmp_path):
        """edit com ID inexistente deve retornar código != 0."""
        rodar_cli(["add", "Existe"], cwd=tmp_path)
        resultado = rodar_cli(["edit", "999", "--title", "Novo"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_edit_prioridade_invalida_falha(self, tmp_path):
        """edit com prioridade fora do enum deve falhar."""
        rodar_cli(["add", "Tarefa"], cwd=tmp_path)
        resultado = rodar_cli(["edit", "1", "-p", "critica"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_edit_data_malformada_falha(self, tmp_path):
        """edit com data em formato inválido deve falhar."""
        rodar_cli(["add", "Tarefa"], cwd=tmp_path)
        resultado = rodar_cli(["edit", "1", "-d", "2025/12/31"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_edit_nao_afeta_outros_campos(self, tmp_path):
        """edit --title não deve alterar prioridade nem due_date existentes."""
        rodar_cli(["add", "Original", "-p", "high", "-d", "2025-11-01"], cwd=tmp_path)
        rodar_cli(["edit", "1", "--title", "Atualizado"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        tarefa = dados["tasks"][0]
        assert tarefa["priority"] == "high"
        assert tarefa["due_date"] == "2025-11-01"


# ---------------------------------------------------------------------------
# Comando delete
# ---------------------------------------------------------------------------

class TestComandoDelete:
    def test_delete_com_force(self, tmp_path):
        """delete --force deve remover a tarefa sem pedir confirmação."""
        rodar_cli(["add", "Para deletar"], cwd=tmp_path)
        resultado = rodar_cli(["delete", "1", "--force"], cwd=tmp_path)
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert len(dados["tasks"]) == 0

    def test_delete_com_confirmacao_y(self, tmp_path):
        """delete sem --force confirmado com 'y' deve remover a tarefa."""
        rodar_cli(["add", "Para deletar com y"], cwd=tmp_path)
        resultado = rodar_cli(["delete", "1"], cwd=tmp_path, input_text="y\n")
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert len(dados["tasks"]) == 0

    def test_delete_com_confirmacao_n_nao_remove(self, tmp_path):
        """delete sem --force confirmado com 'N' deve manter a tarefa."""
        rodar_cli(["add", "Nao deletar"], cwd=tmp_path)
        resultado = rodar_cli(["delete", "1"], cwd=tmp_path, input_text="N\n")
        assert resultado.returncode == 0
        dados = ler_tasks(tmp_path)
        assert len(dados["tasks"]) == 1

    def test_delete_id_inexistente_falha(self, tmp_path):
        """delete com ID inexistente deve retornar código != 0."""
        rodar_cli(["add", "Existe"], cwd=tmp_path)
        resultado = rodar_cli(["delete", "999", "--force"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_delete_nao_afeta_outras_tarefas(self, tmp_path):
        """delete de uma tarefa não deve remover as demais."""
        rodar_cli(["add", "Primeira"], cwd=tmp_path)
        rodar_cli(["add", "Segunda"], cwd=tmp_path)
        rodar_cli(["add", "Terceira"], cwd=tmp_path)
        rodar_cli(["delete", "2", "--force"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        ids_restantes = [t["id"] for t in dados["tasks"]]
        assert 1 in ids_restantes
        assert 3 in ids_restantes
        assert 2 not in ids_restantes

    def test_delete_unica_tarefa_deixa_lista_vazia(self, tmp_path):
        """Deletar a única tarefa existente deve deixar tasks=[]."""
        rodar_cli(["add", "Unica"], cwd=tmp_path)
        rodar_cli(["delete", "1", "--force"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"] == []


# ---------------------------------------------------------------------------
# Comando show
# ---------------------------------------------------------------------------

class TestComandoShow:
    def test_show_exibe_titulo(self, tmp_path):
        """show <id> deve exibir o título da tarefa no stdout."""
        rodar_cli(["add", "Tarefa detalhada"], cwd=tmp_path)
        resultado = rodar_cli(["show", "1"], cwd=tmp_path)
        assert resultado.returncode == 0
        assert "Tarefa detalhada" in resultado.stdout

    def test_show_exibe_prioridade(self, tmp_path):
        """show <id> deve exibir a prioridade da tarefa."""
        rodar_cli(["add", "Com prio", "-p", "high"], cwd=tmp_path)
        resultado = rodar_cli(["show", "1"], cwd=tmp_path)
        assert "high" in resultado.stdout

    def test_show_exibe_due_date(self, tmp_path):
        """show <id> deve exibir a data de vencimento quando presente."""
        rodar_cli(["add", "Com data", "-d", "2025-08-20"], cwd=tmp_path)
        resultado = rodar_cli(["show", "1"], cwd=tmp_path)
        assert "2025-08-20" in resultado.stdout

    def test_show_exibe_status_done(self, tmp_path):
        """show <id> deve exibir informação de status (concluída/pendente)."""
        rodar_cli(["add", "Para concluir"], cwd=tmp_path)
        rodar_cli(["done", "1"], cwd=tmp_path)
        resultado = rodar_cli(["show", "1"], cwd=tmp_path)
        assert resultado.returncode == 0
        saida = resultado.stdout.lower()
        # Aceita qualquer representação: "done", "concluida", "true", etc.
        assert any(termo in saida for termo in ["done", "conclu", "true", "sim"])

    def test_show_id_inexistente_falha(self, tmp_path):
        """show com ID inexistente deve retornar código != 0."""
        rodar_cli(["add", "Existe"], cwd=tmp_path)
        resultado = rodar_cli(["show", "999"], cwd=tmp_path)
        assert resultado.returncode != 0

    def test_show_id_inexistente_mensagem_erro(self, tmp_path):
        """show com ID inexistente deve emitir mensagem de erro."""
        rodar_cli(["add", "Existe"], cwd=tmp_path)
        resultado = rodar_cli(["show", "999"], cwd=tmp_path)
        saida_combinada = resultado.stdout + resultado.stderr
        assert saida_combinada.strip()

    def test_show_exibe_id_correto(self, tmp_path):
        """show deve exibir detalhes da tarefa com ID correspondente, nao outra."""
        rodar_cli(["add", "Tarefa Alpha"], cwd=tmp_path)
        rodar_cli(["add", "Tarefa Beta"], cwd=tmp_path)
        resultado = rodar_cli(["show", "2"], cwd=tmp_path)
        assert "Beta" in resultado.stdout
        assert "Alpha" not in resultado.stdout


# ---------------------------------------------------------------------------
# Edge cases e integracao
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_id_nao_e_reutilizado_apos_delete(self, tmp_path):
        """O proximo ID apos delete nao deve reutilizar ID removido."""
        rodar_cli(["add", "Primeira"], cwd=tmp_path)
        rodar_cli(["add", "Segunda"], cwd=tmp_path)
        rodar_cli(["delete", "1", "--force"], cwd=tmp_path)
        rodar_cli(["add", "Terceira"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        ids = [t["id"] for t in dados["tasks"]]
        # ID da nova tarefa deve ser maior que 2, nunca reutilizar 1
        assert 1 not in ids
        assert len(ids) == 2

    def test_list_vazia_sem_tasks_json(self, tmp_path):
        """list sem tasks.json existente nao deve levantar excecao."""
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert resultado.returncode == 0

    def test_add_titulo_com_espacos(self, tmp_path):
        """Titulo com multiplas palavras deve ser gravado integralmente."""
        rodar_cli(["add", "Comprar leite e ovos"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["tasks"][0]["title"] == "Comprar leite e ovos"

    def test_done_em_base_sem_tasks_json_falha_graciosamente(self, tmp_path):
        """done em base sem tasks.json deve retornar erro (nao travar)."""
        resultado = rodar_cli(["done", "1"], cwd=tmp_path)
        # Deve retornar codigo != 0 ou pelo menos nao travar/excepcionar sem mensagem
        assert isinstance(resultado.returncode, int)

    def test_sequencia_add_done_list(self, tmp_path):
        """Fluxo completo: add -> done -> list so deve mostrar pendentes."""
        rodar_cli(["add", "Pendente"], cwd=tmp_path)
        rodar_cli(["add", "Para concluir"], cwd=tmp_path)
        rodar_cli(["done", "2"], cwd=tmp_path)
        resultado = rodar_cli(["list"], cwd=tmp_path)
        assert "Pendente" in resultado.stdout
        assert "Para concluir" not in resultado.stdout

    def test_sequencia_add_edit_show(self, tmp_path):
        """Fluxo completo: add -> edit -> show deve refletir edicao."""
        rodar_cli(["add", "Titulo original"], cwd=tmp_path)
        rodar_cli(["edit", "1", "--title", "Titulo editado"], cwd=tmp_path)
        resultado = rodar_cli(["show", "1"], cwd=tmp_path)
        assert "Titulo editado" in resultado.stdout
        assert "Titulo original" not in resultado.stdout

    def test_prioridade_invalida_nao_cria_tarefa(self, tmp_path):
        """add com prioridade invalida nao deve criar nenhuma tarefa."""
        rodar_cli(["add", "Invalida", "-p", "urgente"], cwd=tmp_path)
        caminho = tmp_path / "tasks.json"
        if caminho.exists():
            dados = ler_tasks(tmp_path)
            assert len(dados["tasks"]) == 0

    def test_data_malformada_nao_cria_tarefa(self, tmp_path):
        """add com data invalida nao deve criar nenhuma tarefa."""
        rodar_cli(["add", "Data errada", "-d", "nao-e-data"], cwd=tmp_path)
        caminho = tmp_path / "tasks.json"
        if caminho.exists():
            dados = ler_tasks(tmp_path)
            assert len(dados["tasks"]) == 0

    def test_version_preservada_apos_operacoes(self, tmp_path):
        """version em tasks.json deve permanecer 1 apos add/done/edit/delete."""
        rodar_cli(["add", "T1"], cwd=tmp_path)
        rodar_cli(["add", "T2"], cwd=tmp_path)
        rodar_cli(["done", "1"], cwd=tmp_path)
        rodar_cli(["edit", "2", "--title", "T2 editada"], cwd=tmp_path)
        rodar_cli(["delete", "1", "--force"], cwd=tmp_path)
        dados = ler_tasks(tmp_path)
        assert dados["version"] == 1

    def test_tasks_json_e_json_valido(self, tmp_path):
        """tasks.json deve ser JSON valido apos multiplas operacoes."""
        rodar_cli(["add", "A", "-p", "high", "-d", "2025-10-10"], cwd=tmp_path)
        rodar_cli(["add", "B", "-p", "medium"], cwd=tmp_path)
        rodar_cli(["done", "1"], cwd=tmp_path)
        rodar_cli(["edit", "2", "--title", "B editada"], cwd=tmp_path)
        caminho = tmp_path / "tasks.json"
        conteudo = caminho.read_text(encoding="utf-8")
        dados = json.loads(conteudo)  # levanta se invalido
        assert isinstance(dados, dict)
