---
slug: cua 
title: Detalhamento do CUA
authors: [eduardo]
---

Durante meu estágio na empresa [Opus Software](https://www.opus-software.com.br/),
fui encarregado de realizar um estudo detalhado sobre o funcionamento de CUAs
e seu caso de uso no cenário crescente do uso de IA generativa.

Pela definição da OpenAI, um Computer Using Agent (CUA) é um modelo que
combina os recursos de visão de um LLM com raciocínio avançado por meio da 
aprendizagem por reforço (RL). Esses agentes são capazes de interagir com 
ambientes computacionais, como sistemas operacionais, navegadores da web 
e aplicativos, para realizar tarefas complexas que exigem múltiplas etapas.

A Anthropic define como um agente autônomo que pode seguir os comandos do usuário 
para mover o cursor pela tela do computador, clicar em locais relevantes e inserir 
informações por meio de um teclado virtual, emulando a forma como as pessoas 
interagem com seus próprios computadores.

Abaixo um esquema visual representando o fluxo de ações de um CUA:

![Fonte: OpenAI](/img/cua/cua-diagram.webp)

## Origem

O conceito de CUA surgiu meados do fim de 2024, quando a Anthropic anunciou
o Computer Use junto de seus novos modelos Claude 3.5 Sonnet e Claude 3.5
Haiku. A Anthropic disponibilizou uma [API](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)
dedicada para o Computer Use como tool para seus próprios modelos.

## Motivação

Eles surgiram como uma alternativa aos RPAs (Robotic Process Automations),
que dependem de scripts rígidos e pré-definidos para automatizar tarefas.

Um RPA é uma tecnologia de software para automatizar tarefas digitais de
forma rápida e confiável, porém muito rígida. A RPA ainda é uma tecnologia central para 
viabilizar a automação empresarial, trabalhando (ou não) ao lado de ferramentas de IA, 
incluindo IA generativa.

### Tipos de RPA

![Comparativo entre RPA Assistida e Não Assistida](/img/cua/rpa-attended-vs-unattended.avif)
<sub>Fonte: Digital Bricks</sub>

#### RPA Assistida

A **RPA Assistida** é utilizada para auxiliar trabalhadores humanos com 
tarefas rotineiras. Esta forma de RPA depende de gatilhos ou entradas para 
iniciar tarefas automatizadas específicas. Os bots de RPA assistida necessitam
operar com auxílio de intervenção humana. Eles são frequentemente empregados em
cenários de front-office, como atendimento ao cliente, suporte técnico e
processamento de transações.

Exemplos de ferramentas para **RPA assistida** incluem:

- [Microsoft Power Automate](https://make.powerautomate.com/)
- [UiPath](https://www.uipath.com/pt/product/studio)

#### RPA Não Assistida

A **RPA não assistida**, como o nome sugere, opera sem intervenção humana. 
Essas automações funcionam de forma independente com base em gatilhos, 
entradas de dados e cronogramas pré-programados. A RPA não assistida pode ser
acionada e operar em segundo plano, sendo mais frequentemente aplicada a 
processos de back-office, como entrada de dados, processos de TI e 
integrações de aplicativos.

Exemplos de ferramentas para **RPA não assistida** incluem:

- [Blue Prism](https://www.blueprism.com/)
- [Microsoft Power Automate](https://make.powerautomate.com/)
- [UiPath](https://www.uipath.com/pt/product/studio)

#### Paralelo com CUAs

Os CUAs diferem dos RPAs na forma como interagem com sistemas: enquanto RPAs 
seguem scripts pré-definidos baseados em regras rígidas, CUAs utilizam modelos de IA 
para interpretar interfaces visuais e tomar decisões dinâmicas:

**Quando usar RPAs:**
- Processos altamente estruturados e repetitivos (ex: migração de dados entre 
sistemas, processamento de faturas padronizadas)
- Interfaces estáveis que raramente mudam
- Requisitos de auditoria rigorosos que exigem execução determinística
- Alto volume de transações idênticas
- Ambientes onde previsibilidade e velocidade são críticas

**Quando usar CUAs:**
- Processos que envolvem múltiplas aplicações sem APIs integradas
- Interfaces que sofrem atualizações frequentes de layout
- Tarefas que requerem interpretação contextual e tomada de decisão
- Automações que precisam ser configuradas rapidamente sem programação extensa
- Cenários onde a interface varia entre execuções (ex: sites de terceiros, 
aplicações legacy)

## Resultados da pesquisa

Na pesquisa que desenvolvi dentro da empresa, cheguei a algumas conclusões importantes,
baseadas em experiência própria de uso e em benchmarks consolidados em pesquisas públicas:

### Resultados de CUAs em benchmarks dedicados

Existem benchmarks dedicados para avaliar CUAs em diferentes contextos. Os principais
avaliados na pesquisa foram:

- **[OS World](https://os-world.github.io/)** — 369 tarefas abertas em sistemas
operacionais reais. O melhor modelo avaliado em 18/12/2025 foi o
`claude-sonnet-4-5-20250929` com **62.9%** de taxa de sucesso.

- **[REAL](https://arxiv.org/pdf/2504.11543)** — 112 tarefas práticas em réplicas
determinísticas de 11 sites populares (e-commerce, viagens, etc.). Os melhores modelos
atingem no máximo **41%** de taxa de sucesso, evidenciando limitações críticas na
navegação web autônoma.

- **[Online Mind2Web](https://hal.cs.princeton.edu/online_mind2web)** — versão ao
vivo do Mind2Web, que testa agentes contra interfaces web dinâmicas em tempo real. O
melhor resultado registrado em 09/01/2026 foi do GPT-5 Medium com **42.33%** de sucesso
usando o framework SeeAct.

- **[WebVoyager](https://arxiv.org/abs/2401.13919)** — navegação autônoma em 15
categorias de sites reais. O Magnitude liderou em 09/01/2026 com **93.9%** de sucesso,
seguido por frameworks como Browser Use e Convergence Proxy.

- **[AndroidWorld](https://google-research.github.io/android_world/)** — 116 tarefas
em 20 aplicativos Android reais. O AGI-0 liderou em 10/2025 com **97.4%** de sucesso;
o agente M3A (linha de base original do benchmark) completou apenas **30.6%** das
tarefas.

### Limitações de CUAs

Apesar dos avanços significativos, os CUAs ainda enfrentam várias limitações. Dentre
as principais, podemos destacar:

- A interação com interfaces gráficas e a necessidade de múltiplas etapas podem 
resultar em **latências significativas**, mesmo em tarefas simples, como
usar a calculadora ou abrir o navegador e pesquisar algo. Por isso é importante focar
a intenção de uso do CUA em tarefas que não sejam críticas em termos de tempo.
- A limitada precisão da **visão computacional** no reconhecimento de elementos na 
tela pode variar, ocasionando no CUA entrando em loop por tentar clicar em um elemento
na coordenada incorreta várias vezes seguidas, ou mesmo não conseguir identificar
elementos importantes.
- Muitos modelos possuem **guard rails rígidos** para evitar ações indesejadas, o que 
pode levar a muitos pedidos de confirmação para ações simples, atrapalhando a 
fluidez da automação.
- A tecnologia de CUAs ainda está em **estado experimental e sensível**, com muitas
ferramentas e frameworks em desenvolvimento ativo. Isso pode levar a bugs, falta de
recursos e mudanças frequentes/falta de informação relevante nas APIs e documentação.

### Arquétipos de Falha Comuns:

Segundo análises de implementações nos benchmarks, as falhas dos CUAs geralmente se 
enquadram em alguns arquétipos comuns:

1. O agente faz uma **suposição incorreta** no início da tarefa e não a 
questiona posteriormente.
2. O agente faz **decisões razoáveis** como se estivesse ajudando um usuário real, 
mas **falha em atender requisitos estritos da tarefa**
3. O agente responde com base em seu **conhecimento de pré-treinamento**, em vez de 
buscar informações no navegador.
4. Falha em responder dentro de um **período de tempo razoável**, devido a complexidade
e quantidade de passos necessária para cumprir uma determinada tarefa.

## Conclusões

Os CUAs representam um avanço relevante na automação de tarefas digitais complexas,
mas a tecnologia ainda está em estado claramente experimental. 
Mesmo tarefas simples podem falhar por imprecisão na visão computacional, 
loops de ação, guard rails excessivos ou simples desvios de raciocínio. 
Os benchmarks realizados mostram que até mesmo os melhores modelos de linguagem
raramente ultrapassam 60–70% de taxa de sucesso em ambientes controlados, e o
desempenho cai consideravelmente em cenários do mundo real.

Dessa forma, o escopo de uso de CUAs no contexto deste TCC deve ser limitado ao
mínimo necessário: no máximo, servir como avaliador comportamental de caixa-preta
para testes pontuais do resultado final do pipeline multiagente a ser construído,
verificando se o software gerado se comporta corretamente do ponto de vista de um
usuário real, sem assumir que o CUA executará essas verificações de forma confiável
em todos os casos.
