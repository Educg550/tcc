---
slug: agent-skills
title: "Agent Skills: overview do padrão"
authors: [eduardo]
tags: [referencia]
---

**Agent Skills** é um padrão aberto de criação e gerenciamento de conhecimento e especializações para agentes de IA.
Ele foi criado pela Anthropic e é mantido por ela e pela comunidade.
O [repositório oficial](https://github.com/agentskills/agentskills) contém a documentação oficial de uso
e alguns exemplos de Skills criadas pela Anthropic.
As Skills têm como objetivo fornecer melhor contexto para os agentes de IA,
permitindo que eles sejam mais eficientes e precisos em suas tarefas.

<!-- truncate -->

## O que é uma Skill?

Uma **Skill** é basicamente um diretório.
Esse diretório pode ser estruturado de acordo com as necessidades do desenvolvedor,
desde que siga a premissa básica de ter um arquivo `SKILL.md` que descreva a Skill.
Fora isso, o diretório pode ter quaisquer outros arquivos relevantes para a Skill.
Isso inclui, mas não se limita a:

- Arquivos de código-fonte (`*.py`, `*.js`, etc.)
- Arquivos de configuração (`*.yaml`, `*.json`, etc.)
- Arquivos de dados (`*.csv`, `*.xlsx`, etc.)
- Arquivos de mídia (`*.png`, `*.jpg`, etc.)

## Como o SKILL.md é estruturado?

O `SKILL.md` é o único arquivo obrigatório de uma Skill.
Ele deve conter um frontmatter YAML seguido de conteúdo Markdown.

```yaml
---
name: nome-da-skill        # obrigatório: lowercase, hífens, máx 64 chars
description: Descrição...  # obrigatório: o que faz e quando usar, máx 1024 chars
# TODOS os campos abaixo são opcionais
license: Apache-2.0
metadata:                  # metadados arbitrários
  author: meu-org
  version: "1.0"
compatibility: Requires git # requisitos de ambiente
allowed-tools: Bash Read    # tools pré-aprovadas (ex: Claude Code)
---

# Conteúdo Markdown com instruções para o agente
```

O `name` deve corresponder exatamente ao nome do diretório da Skill.
Esse será o nome que o agente utilizará para identificar a Skill.

## Quais diretórios uma Skill pode ter?

Além do `SKILL.md`, uma Skill pode incluir qualquer arquivo ou diretório relevante.
A especificação oficial define três diretórios com nomes e semânticas padronizadas,
que agentes compatíveis reconhecem e tratam de forma especial:

| Diretório | Finalidade |
|-----------|-----------|
| `scripts/` | Código executável (Python, Bash, etc.) para tarefas repetitivas ou que exigem confiabilidade determinística |
| `references/` | Documentação carregada sob demanda pelo agente (schemas, políticas, guias técnicos) |
| `assets/` | Arquivos usados na saída gerada (templates, imagens, fontes) |

Esses nomes **não são obrigatórios**.
A spec não impede a criação de outros diretórios com nomes arbitrários.
A convenção existe para garantir interoperabilidade entre diferentes implementações de agentes:
um agente compatível sabe que pode executar scripts em `scripts/`, carregar referências de `references/`
e copiar assets de `assets/` sem precisar de instrução explícita no `SKILL.md`.

## Como usar Skills com agentes compatíveis?

Para usar uma Skill, é preciso um agente compatível com o padrão.
Alguns dos mais conhecidos:

| Agente | Tipo |
|--------|------|
| [Claude Code](https://claude.ai/code) | CLI / editor |
| [Cursor](https://cursor.sh) | Editor |
| [GitHub Copilot](https://github.com/features/copilot) | Editor / CLI |
| [Goose](https://block.github.io/goose/) | Desktop / CLI |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | Agente autônomo |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | CLI |

Ao iniciar, o agente escaneia os diretórios configurados em busca de subdiretórios com `SKILL.md`
e carrega apenas o frontmatter (`name` + `description`) de cada um no contexto do sistema.
Durante uma tarefa, o agente decide por conta própria quais Skills são relevantes
e carrega o corpo completo do `SKILL.md` das selecionadas.

Existem duas abordagens de integração:

- **Filesystem-based** — o agente opera em um ambiente Unix e acessa os arquivos da Skill
  via comandos de shell (`cat`, `python scripts/...`).
  É a abordagem mais completa, pois permite execução direta de scripts.
- **Tool-based** — o agente não tem acesso direto ao sistema de arquivos
  e implementa ferramentas próprias para carregar e executar os recursos da Skill.

Qualquer SDK pode adicionar suporte a Skills
seguindo o [guia de integração oficial](https://agentskills.io/integrate-skills).

## Como a Anthropic usa Skills em cada uma de suas plataformas?

A Anthropic disponibiliza Skills como **artefatos versionáveis e modulares**,
com quatro pontos de acesso principais: **Claude API**, **Claude Code**, **Claude Agent SDK** e **Claude.ai / Claude Desktop**.
Todos seguem o mesmo modelo conceitual —
a diferença entre as plataformas está apenas na superfície de gerenciamento e carregamento da Skill.

| Aspecto | Claude API | Claude Code | Agent SDK | Claude.ai / Desktop |
|---------|------------|-------------|-----------|---------------------|
| Registro | Via API (workspace) | Arquivo local | Arquivo local | Upload ZIP via GUI |
| Versionamento | Explícito | Git | Git | Reupload |
| Execução | Container isolado | Runtime CLI | Runtime SDK | Container isolado |
| Controle de tools | Via request | Frontmatter | `allowed_tools` | Via GUI |
| Disclosure progressivo | Sim | Sim | Sim | Sim |

### Claude API

Na API, Skills são **recursos do workspace**, gerenciados via CRUD
e executados dentro de um container de `code_execution`.
O container garante isolamento total: sem acesso à rede, ambiente reprodutível,
com suporte a até 8 Skills por requisição.
Cada Skill possui versões imutáveis — em produção, sempre use versões fixas.

Para usar Skills via API, é necessário habilitar os betas `code-execution-*` e `skills-*`.
O registro é feito via `client.beta.skills.create`
e a inclusão na requisição é feita via o parâmetro `container.skills`.

```python
import anthropic
from anthropic.lib import files_from_dir

client = anthropic.Anthropic()

# Registrando a Skill no workspace
skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=files_from_dir("/path/to/financial_analysis_skill"),
    betas=["skills-2025-10-02"],
)

# Utilizando a Skill em uma requisição
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=512,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "custom",
            "skill_id": skill.id,
            "version": skill.version,
        }]
    },
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution",
    }],
    messages=[{
        "role": "user",
        "content": "Create a simple Excel budget file",
    }]
)

print(response.content)
```

### Claude Code

No Claude Code, Skills são **artefatos locais no filesystem**.
O escopo determina onde o agente procura por Skills:

| Escopo | Caminho |
|--------|---------|
| Usuário | `~/.claude/skills/` |
| Projeto | `.claude/skills/` |
| Enterprise | Managed settings |

A prioridade de carregamento segue a ordem: `enterprise > user > project`.
A invocação pode ser automática — o agente detecta a Skill relevante pela descrição —
ou manual, via comando explícito:

```bash
/skill-name faça X, Y e Z com essa Skill
```

Para executar uma Skill em contexto isolado, sem acesso ao histórico principal,
configure o frontmatter com:

```yaml
context: fork
agent: Explore
```

### Claude Agent SDK

No SDK, Skills também são carregadas do filesystem,
mas **não existe API para registrá-las**: elas devem estar presentes no filesystem
que está executando o script.
Há três escopos disponíveis:

- **Project Skills** (`.claude/skills/`) — compartilhadas via git com a equipe;
  carregadas quando `setting_sources` inclui `"project"`.
- **User Skills** (`~/.claude/skills/`) — Skills pessoais, disponíveis em todos os projetos;
  carregadas quando `setting_sources` inclui `"user"`.
- **Plugin Skills** — empacotadas com plugins instalados do Claude Code.

Para usar Skills no SDK, é obrigatório configurar `setting_sources`
e incluir `"Skill"` em `allowed_tools`.
O campo `allowed-tools` do frontmatter **não se aplica no SDK**.

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        cwd="/path/to/project",
        setting_sources=["user", "project"],  # Define o escopo onde procurar por Skills
        allowed_tools=["Skill", "Read", "Bash"]
    )

    async for msg in query(
        prompt="What skills are available?",
        options=options
    ):
        print(msg)

asyncio.run(main())
```

### Claude.ai e Claude Desktop

No Claude.ai e no Claude Desktop, Skills são **pacotes ZIP carregados via interface gráfica**,
executados em container sandboxed — o mesmo ambiente isolado usado pela Claude API.
O pré-requisito é que a opção `Code execution and file creation` esteja habilitada.

Há três categorias de Skills disponíveis nessa superfície:

| Categoria | Exemplos | Como ativar |
|-----------|----------|-------------|
| **Anthropic Skills** (nativas) | Excel, Word, PowerPoint, PDF | Toggle em *Settings* |
| **Custom Skills** | Qualquer Skill em ZIP | *Settings > Capabilities > Skills > Upload skill* |
| **Skills Directory** | Notion, Figma, Atlassian | Download do ZIP + upload manual |

Em planos Team e Enterprise, **owners** podem provisionar Skills para toda a organização
via `Organization settings > Capabilities`.
Usuários individuais podem ativar ou desativar Skills provisionadas
e enviar Skills próprias, que permanecem privadas.

O modelo de ativação segue o mesmo padrão das demais superfícies:
Claude lê `name` e `description` e decide automaticamente se a Skill é relevante.
O usuário pode forçar a ativação com uma instrução explícita:

> "Use my brand guidelines skill to create a presentation"

## Por que usar Skills em vez de MCP Servers?

MCP Servers expõem ferramentas e recursos via protocolo,
exigindo um servidor em execução, configuração de transporte e integração com o cliente.
Skills são arquivos estáticos — sem servidor, sem processo, sem protocolo.

| Aspecto | Agent Skills | MCP Server |
|---------|-------------|------------|
| **Infraestrutura** | Nenhuma — diretório local | Servidor em execução (stdio ou HTTP) |
| **Consumo de tokens** | Sob demanda, por nível de disclosure | Ferramentas listadas no contexto a cada sessão |
| **Acesso ao conhecimento** | Local, offline, sem latência de rede | Requer chamada de ferramenta para cada consulta |
| **Versionamento** | Git nativo — é só um diretório | Depende de versionamento da API ou do servidor |
| **Distribuição** | Copiar ou zipar o diretório | Build, publicação e hospedagem do servidor |

A principal vantagem de custo é o **disclosure progressivo**:
apenas `name` e `description` são carregados por padrão.
O conteúdo completo da Skill entra em contexto somente quando o agente decide que ela é relevante,
e recursos adicionais (`scripts/`, `references/`) somente quando necessários para a tarefa.
Isso permite compor agentes com centenas de Skills simultâneas
sem comprometer a janela de contexto
e reduzindo a chance de alucinações.

MCP Servers continuam sendo a escolha certa quando a Skill precisa de estado persistente,
acesso a sistemas externos em tempo real,
ou operações que dependem de autenticação e conexões de rede.
A desvantagem dos MCPs é o consumo excessivo de tokens na janela de contexto,
que não escala bem quando há necessidade de compor um agente conectado a múltiplos servidores.

## Quais são as boas práticas ao criar uma Skill?

- Escrever o corpo do `SKILL.md` em forma imperativa ("Responder com...", "Executar o script...")
- Manter o `SKILL.md` abaixo de 500 linhas; mover material de referência detalhado para `references/`
- Usar `description` com palavras-chave que ajudem o agente a identificar quando ativar a Skill
- Deletar diretórios opcionais que não forem utilizados

## Referências

- [Curso: Agent Skills with Anthropic — DeepLearning.AI](https://www.deeplearning.ai/short-courses/agent-skills-with-anthropic/)
- [Repositório oficial do padrão Agent Skills](https://github.com/agentskills/agentskills)
- [Site oficial do padrão Agent Skills](https://agentskills.io/)
