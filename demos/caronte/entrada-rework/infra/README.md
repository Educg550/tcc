# Infraestrutura compartilhada

Os esquemas SQL são dumps sem dados dos bancos do original congelado
`46b89c1d5519aeae40c088ee94262e9b739a7d48`. As funções SQL do forms fazem
parte dessa infraestrutura e não precisam ser reimplementadas. O banco do
prejanus também já existe, com o esquema fornecido. Não criar, apagar ou
migrar tabelas na inicialização da aplicação.

Os demais SQLs são os dados declarativos da fixture; o formulário JSON
documenta as seções, campos, tipos e rótulos. Esses arquivos explicam o
contrato dos bancos, não substituem consultas: ler as respostas e os
usuários dos bancos, e os anexos do volume, sem fixar valores da fixture
no código. As fixtures já são carregadas pelo avaliador antes de iniciar
a aplicação.

A aplicação recebe as variáveis de ambiente do original:

- `DB_CONNECTION_STRING`: URL SQLAlchemy `postgresql+psycopg://...` do banco
  do prejanus.
- `DB_CONNECTION_STRING_FORMS`: mesma forma de URL, com usuário de leitura
  do banco do forms.
- `APP_ENV` e `DEV_USER_ID`: o atalho de autenticação vale somente quando
  `APP_ENV=local`. Sem o atalho e sem sessão, responder 401 nas rotas
  protegidas.
- Os arquivos enviados ficam em `/shared/uploads/`.

Os serviços compartilham a rede Docker `shared_network`; o host do banco
nessa rede é `db`, porta 5432. Credenciais e nomes dos bancos vêm das URLs
de ambiente. O avaliador pode selecionar outros bancos com os mesmos
esquemas e dados.

