# Skills para o piloto

Pesquisa em 16/10/2026 com o catálogo skills.sh e conferência dos repositórios
originais. A tentativa de `npx skills find flask` falhou por DNS do npm; a
busca prosseguiu pelo catálogo web. Os arquivos foram baixados para `/tmp`
apenas para inspeção, sem instalação nem execução das skills.

O [manifesto](./skills.lock.json) fixa o commit completo, o diretório, o Git
tree desse diretório, o SHA-256 do `SKILL.md` e as evidências de licença.
É um manifesto próprio do piloto, não o formato de lock gerado pelo CLI
Skills. A identificação por commit vale também para as referências e assets
contidos no diretório; a versão declarada no frontmatter não basta sozinha.

## Seleção

Contagens de instalações são aproximadas, informadas pelo catálogo, e podem
refletir páginas coletadas em momentos diferentes. Estrelas foram consultadas
diretamente no GitHub. Popularidade auxilia a seleção, sem substituir a
leitura do conteúdo ou da licença.

| Área | Skill e origem | Instalações | Estrelas do repo | Revisão fixada | Licença declarada |
|---|---|---:|---:|---|---|
| Simplicidade | [ponytail — DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/releases/tag/v5.3.1) | não obtida | 165.076 | **5.3.1**, `6f1c2bfff0c8` | MIT, arquivo LICENSE |
| Flask/Jinja | [flask — jezweb/claude-skills](https://www.skills.sh/jezweb/claude-skills/flask) | ~430 | 1.067 | `75f67bc67104` | MIT, arquivo LICENSE |
| FastAPI/Pydantic | [fastapi — fastapi/fastapi](https://www.skills.sh/fastapi/fastapi/fastapi) | ~12,4 mil | 103.143 | `4fce9ce17291` | MIT, arquivo LICENSE |
| React | [vercel-react-best-practices — vercel-labs/agent-skills](https://www.skills.sh/vercel-labs/agent-skills/vercel-react-best-practices) | ~808 mil | 32.523 | `1.0.0`, `063bee94c3f4` | MIT declarada no SKILL.md e README; sem LICENSE separado |
| Next | [next-best-practices — vercel-labs/openreview](https://www.skills.sh/vercel-labs/openreview/next-best-practices) | ~5,7 mil | 1.693 | `672deb21e70e` | MIT declarada no README; sem LICENSE separado |
| Material UI/Next | [material-ui-nextjs — mui/material-ui](https://www.skills.sh/mui/material-ui/material-ui-nextjs) | ~700 | 99.226 | `1.0.0`, `25080a9316c1` | MIT, arquivo LICENSE |
| Postgres | [supabase-postgres-best-practices — supabase/agent-skills](https://www.skills.sh/supabase/agent-skills/supabase-postgres-best-practices) | ~447 mil | 2.849 | `1.1.1`, `c9be0e931b79` | MIT, arquivo LICENSE |
| Docker Compose | [docker-compose-patterns — docker/skills](https://www.skills.sh/docker/skills/docker-compose-patterns) | ~936 | 569 | `25f7e03184ce` | Apache-2.0, arquivo LICENSE e frontmatter |
| pytest | [python-testing-patterns — wshobson/agents](https://www.skills.sh/wshobson/agents/python-testing-patterns) | ~35,9 mil | 40.912 | `044b4b21f083` | MIT, arquivo LICENSE |
| Cypress | [cypress-author — cypress-io/ai-toolkit](https://www.skills.sh/cypress-io/ai-toolkit/cypress-author) | ~7,4 mil | 46 | `1.0.1`, `da6ea17dfa67` | MIT, arquivo LICENSE |

Os oito primeiros formam a proposta de apoio à implementação; os dois
últimos apoiam autoria de testes. A skill Cypress vem do mantenedor do
framework, embora o repositório de skills ainda tenha menos de 100 estrelas.
Flask, MUI e Docker têm menos de mil instalações; foram mantidos por adequação
ao problema e, nos dois últimos casos, origem oficial. Isso não comprova
eficácia no modelo usado pelo piloto.

## Escolha das revisões e compatibilidade

- **Ponytail:** usar somente `skills/ponytail` da release 5.3.1. Não instalar
  hooks, plugin, comandos de auditoria ou interface da extensão. O pacote
  já disponível localmente declara 5.3.1, e seu SKILL.md coincide com o
  arquivo da release. O piloto usa o nível full, o padrão da skill: nada a
  configurar no harness. A sessão de preparação estava em ultra.
- **Flask:** o ramo atual removeu essa skill em fevereiro. Foi recuperada
  a revisão de 20/01/2026 que ainda contém o diretório completo e a licença.
  Ela recomenda Flask-SQLAlchemy, Flask-Login e Flask-WTF; essas sugestões
  não autorizam trocar o psycopg, o acesso público do candidato ou o CSRF
  do original. Preservar as dependências e o contrato escolhidos no projeto.
- **FastAPI:** a revisão inicial da skill, de 25/02/2026, evita a inclusão
  posterior de SSE, frontend nativo e OpenTelemetry. Ainda recomenda
  ferramentas e configuração próprias: o comando Uvicorn, as versões
  instaladas e o contrato do piloto prevalecem. Não migrar SQLAlchemy para
  SQLModel por recomendação da skill.
- **Next/React/MUI:** o original declara Next 15.5.7, React 19 e MUI 7.
  Aplicar somente orientações compatíveis; exemplos de Next 16 não autorizam
  renomear middleware para proxy nem atualizar o framework.
- **Postgres/Docker:** as regras não autorizam redesenhar o esquema que a
  fixture SQL compartilha, trocar serviços/imagens congelados, renomear os
  arquivos Compose usados pelo roteiro ou apagar volumes.
- **pytest/Cypress:** usar os frameworks e versões do projeto. O Cypress
  Author pode pedir esclarecimentos e depende de seus subskills; a etapa
  automatizada precisa receber tarefa e contexto completos. Os gates são
  executados pelo harness, sem conceder bash aos agentes.

Não entrou na seleção `yonatangross/orchestkit@python-backend` na revisão
`0bb1ebb63526b568f4802f36079c411e056a6985`: o frontmatter exige FastAPI
`>=0.142.2`, SQLAlchemy `>=2.1.1` e Claude Code recente. Essas exigências
não correspondem ao backend original nem ao executor opencode previsto.
As opções encontradas para Celery/Redis eram específicas de outros sistemas
ou pouco verificadas; não acrescentam uma skill ao pacote nesta seleção.
Não foi selecionada uma skill específica de SQLAlchemy: sua documentação
compatível com a versão do projeto continua sendo a referência necessária.

## Licenças e distribuição

As evidências abaixo correspondem aos commits do manifesto, não às licenças
das bibliotecas que as skills ensinam. A licença do pacote não deve ser
inferida da licença de Flask, Cypress ou outro framework.

Para as oito entradas com arquivo LICENSE, o arquivo foi lido no commit
fixado e seu hash foi registrado. Os diretórios completos foram inspecionados
quanto a arquivos de licença/NOTICE e cabeçalhos de atribuição. Não foram
localizadas licenças diferentes dentro desses diretórios nem arquivo NOTICE
adicional no índice dos repositórios selecionados. Isso descreve a inspeção
realizada; não é uma garantia sobre a titularidade de todo exemplo upstream.

**MIT:** ao copiar ou distribuir os materiais, conservar o texto da licença
e os avisos de copyright/atribuição existentes. Os autores nos LICENSE são
DietrichGebert, Jeremy Dawes (Jezweb), Sebastián Ramírez, Call-Em-All, Supabase,
Seth Hobson e Cypress.io, conforme a entrada correspondente.

**Docker/Apache-2.0:** conservar LICENSE e avisos aplicáveis; se houver
modificações, identificá-las. Preservar NOTICE quando existir. No commit
consultado, não foi localizado NOTICE separado. A seleção não modifica o
conteúdo da skill.

**Duas ressalvas de empacotamento:** React declara MIT no próprio SKILL.md e
no README; Next declara MIT no README. Nenhum dos dois repositórios contém
um arquivo LICENSE separado no índice da revisão consultada, e a API GitHub
não reconhece uma licença nesses repositórios. O manifesto distingue
`declaration_only` de `license_file`; não registra um texto de licença nem
um titular que não foram encontrados. As duas cópias levam um `ATTRIBUTION.md`
que aponta a declaração MIT no commit fixado, com o README copiado em `_origem/`.

O CLI pode copiar apenas o diretório da skill, deixando LICENSE e README
na raiz do repositório de origem. Por isso as skills não são instaladas pelos
comandos abaixo: `vendorizar.py` materializa cada uma em `skills/<nome>/` no
commit do manifesto, confere a árvore git e o SHA-256 do SKILL.md, e copia as
evidências de licença de fora do diretório da skill para `_origem/`.

## Entrada dos agentes e orçamento

Recomenda-se disponibilizar o mesmo inventário técnico, nas mesmas revisões,
para baseline, TDD e rework, com carregamento sob demanda. Não concatenar
todos os guias e regras no prompt inicial. A revisão abrangeu 191 arquivos
(536.314 bytes, incluindo evidências de licença); esse volume não é uma
estimativa de tokens nem precisa ser carregado integralmente por etapa.

O protocolo do grupo e as restrições do harness prevalecem sobre as skills.
Em particular, o Ponytail pede um teste para lógica nova, e a skill pytest
discute TDD: isso não acrescenta escrita/execução de testes, feedback de gate
ou iteração à baseline. A autoria de testes só é ativada nas etapas que a
preveem. Nenhum agente ganha bash ou acesso ao gabarito escondido.

O diretório fornecido a cada run deve ser isolado das skills globais e do
ambiente pessoal de preparação. Não atualizar skills durante runs. Links
para documentação remota não são congelados pelo commit da skill: qualquer
documentação adicional disponibilizada precisa ser materializada/fixada ou
ter acesso controlado igualmente entre os grupos. Registrar o manifesto e
as skills efetivamente carregadas junto da execução para contabilizar seu
efeito em tokens e custo.

## Comandos de instalação por revisão

A sintaxe de URL GitHub com diretório e seleção de agente é documentada no
[CLI Skills](https://github.com/vercel-labs/skills#source-formats). Os
comandos seguintes ficam para o empacotamento do ambiente isolado do piloto;
não foram executados nem validam a ativação no opencode. Os commits completos
estão nas URLs, inclusive quando a skill também declara uma versão própria.
Resolver as ressalvas de licença antes de redistribuir React/Next.


ponytail:

```bash
npx skills add https://github.com/DietrichGebert/ponytail/tree/6f1c2bfff0c837d268929a7c4e490918eb4fab29/skills/ponytail --skill ponytail --agent opencode --copy --yes
```

fastapi:

```bash
npx skills add https://github.com/fastapi/fastapi/tree/4fce9ce17291423baf68b5ffb7a01a8f344bf08f/fastapi/.agents/skills/fastapi --skill fastapi --agent opencode --copy --yes
```

vercel-react-best-practices:

```bash
npx skills add https://github.com/vercel-labs/agent-skills/tree/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-best-practices --skill vercel-react-best-practices --agent opencode --copy --yes
```

next-best-practices:

```bash
npx skills add https://github.com/vercel-labs/openreview/tree/672deb21e70e471e0536d5ad7a67c14b8359e97e/.agents/skills/next-best-practices --skill next-best-practices --agent opencode --copy --yes
```

supabase-postgres-best-practices:

```bash
npx skills add https://github.com/supabase/agent-skills/tree/c9be0e931b7930f7d02126d04774d904c381e7d7/skills/supabase-postgres-best-practices --skill supabase-postgres-best-practices --agent opencode --copy --yes
```

docker-compose-patterns:

```bash
npx skills add https://github.com/docker/skills/tree/25f7e03184ce455ea1604bea00f7b40f95ca50e5/skills/docker-compose-patterns --skill docker-compose-patterns --agent opencode --copy --yes
```

cypress-author:

```bash
npx skills add https://github.com/cypress-io/ai-toolkit/tree/da6ea17dfa674a2b68908d823e37f5797d5be238/skills/cypress-author --skill cypress-author --agent opencode --copy --yes
```

material-ui-nextjs:

```bash
npx skills add https://github.com/mui/material-ui/tree/25080a9316c1dd5a8af75b152bc8bd3c3ce2b809/skills/material-ui-nextjs --skill material-ui-nextjs --agent opencode --copy --yes
```

flask:

```bash
npx skills add https://github.com/jezweb/claude-skills/tree/75f67bc67104958dc162fbb82a3dfe813523daaa/skills/flask --skill flask --agent opencode --copy --yes
```

python-testing-patterns:

```bash
npx skills add https://github.com/wshobson/agents/tree/044b4b21f083948e69ec878a7b07c8d0951a6ffa/plugins/python-development/skills/python-testing-patterns --skill python-testing-patterns --agent opencode --copy --yes
```
