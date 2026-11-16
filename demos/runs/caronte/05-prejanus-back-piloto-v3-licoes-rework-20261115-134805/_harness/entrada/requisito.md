# Reconstrução guiada pelos testes fornecidos

Implemente do zero a API exercitada pelos testes em `tests/`, em FastAPI e
Postgres. Contratos, esquemas e variáveis estão em `infra/`, inclusive
`infra/README.md` e o OpenAPI de referência. O módulo de entrada é `app.py`,
exportando a aplicação `app`.

O harness executa os testes e devolve as falhas. Não altere os testes, suas
fixtures ou os dados esperados: o gate executa uma cópia própria deles. Você
não executa comandos. Os testes chegam à aplicação pelo proxy HTTPS do
ambiente, em três instâncias: com sessão Senha Única pelo provedor OAuth
local, como docente local (`DEV_USER_ID`) e fora do ambiente local. Eles
também conferem os bancos, a caixa SMTP local e os uploads em `/shared/uploads`.

Use Ponytail no nível full. As regras da etapa prevalecem sobre as skills.

## Organização obrigatória da implementação

Implemente um projeto modular. `app.py` deve apenas criar e configurar a aplicação,
registrar middleware e conectar routers. Separe configuração, conexões dos dois
bancos, autenticação/permissões, routers por domínio e serviços de integração
(Forms, OAuth, e-mail e relatórios). Escolha os nomes e a estrutura de diretórios;
não há um número mínimo artificial de arquivos. Cada módulo deve conter a lógica
da sua responsabilidade, sem depender de um arquivo central com toda a aplicação.

Construa um bloco funcional por vez, escrevendo seus arquivos separadamente pelas
ferramentas e conectando-o aos módulos anteriores. Conclua todos os requisitos
nesta sessão. Não entregue apenas estrutura, stubs ou funcionalidades simuladas.
