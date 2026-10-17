# Reconstrução guiada pelos testes fornecidos

Implemente do zero a API exercitada pelos testes em `tests/`, em FastAPI e
Postgres. Os esquemas e dados declarativos compartilhados estão em `infra/`;
as variáveis de conexão e autenticação estão descritas em `infra/README.md`.
O módulo de entrada é `app.py`, exportando a aplicação `app`.

O harness executa os testes e devolve as falhas. Não altere os testes, suas
fixtures ou os dados esperados. Você não executa comandos. Os testes HTTP
são executados contra duas instâncias da aplicação: uma como docente local
e outra sem o atalho de autenticação. Os uploads ficam em `/shared/uploads`.

Use Ponytail no nível full. As regras da etapa prevalecem sobre as skills.
