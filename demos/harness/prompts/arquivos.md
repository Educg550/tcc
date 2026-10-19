Use as ferramentas para listar e ler o projeto, criar arquivos e substituir trechos.
O conteúdo atual inclui as alterações aceitas nesta sessão. Ao terminar, responda
com um resumo breve; não devolva arquivos nem um JSON na resposta final.

Trabalhe em um bloco funcional pequeno por vez, agrupando requisitos relacionados.
Crie e leia os arquivos desse bloco antes de seguir para o próximo, até cobrir todo
o requisito.

A separação em módulos por responsabilidade é obrigatória quando o projeto tem
múltiplas responsabilidades. Distribua rotas, regras de negócio e acesso a dados
em módulos próprios, com imports explícitos. O ponto de entrada apenas configura
e conecta esses módulos; não concentre a implementação em `app.py` ou equivalente.
Escreva um arquivo por chamada de ferramenta, sem embutir vários arquivos em uma
string ou gerar scripts que escrevem o restante do projeto. A divisão deve conter
implementação real: arquivos vazios ou que só reexportam um monólito não atendem.

Para corrigir um arquivo, leia a versão atual e use `substituir_trecho` com um trecho
exato e único. Preserve o restante. `criar_arquivo` só aceita arquivos novos.
Uma edição Python com sintaxe inválida é recusada: corrija a edição e tente novamente.
Não execute comandos nem scripts. O harness controla a execução e os testes.
