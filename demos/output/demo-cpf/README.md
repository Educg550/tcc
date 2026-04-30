# demo-cpf

Output do pipeline TDD gerado por `demos/orquestrador_claude.py`.

## Como rodar os testes

A partir do diretório `demos/output/demo-cpf/`:

```bash
uv run pytest tests/ -v
```

O `conftest.py` na raiz deste diretório adiciona o path correto automaticamente.
Sem ele, o pytest usa o `pyproject.toml` de `demos/` como rootdir e não encontra `cpf.py`.
