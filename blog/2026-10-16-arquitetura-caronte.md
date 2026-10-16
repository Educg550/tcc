---
slug: arquitetura-caronte
title: "A arquitetura do caronte-core"
authors: [eduardo]
tags: [tcc, referencia]
---

Um resumo de como o caronte-core se organiza, lido do commit congelado em `caronte-core/`.

<!-- truncate -->

O caronte-core é o sistema de inscrições em editais da pós-graduação do IME. O candidato
preenche o formulário e anexa documentos no `forms`, e os recomendadores recebem convite por
e-mail. Depois o docente avalia as inscrições no prejanus. Tudo sobe com um `docker compose`,
atrás de um nginx.

```mermaid
flowchart LR
    C([Candidato / recomendador]) --> N
    D([Docente]) --> N
    N[nginx] -->|"/ e /api"| F["forms<br/>Flask + gunicorn"]
    N -->|/prejanus| PF["prejanus-front<br/>Next"]
    PF -->|REST| PB["prejanus-back<br/>FastAPI"]

    F --> FDB[("Postgres<br/>banco do forms")]
    PB --> PDB[("Postgres<br/>banco do prejanus")]
    PB -.->|leitura| FDB

    F -->|fila de e-mail| R[(Redis)]
    R --> W["celery-worker<br/>envio + limpeza"]
    W --> S[SMTP]
    F -->|varredura| AV[ClamAV]
    F --> U[/uploads compartilhados/]
    PB --> U
    F -.->|login| SU{{Senha Única USP}}
    PB -.->|login| SU

    classDef edge fill:#94a3b8,stroke:#334155,color:#0f172a
    classDef forms fill:#60a5fa,stroke:#1e40af,color:#0f172a
    classDef prejanus fill:#a78bfa,stroke:#5b21b6,color:#0f172a
    classDef data fill:#fbbf24,stroke:#92400e,color:#0f172a
    classDef ext fill:#4ade80,stroke:#166534,color:#0f172a
    class C,D,N edge
    class F,W forms
    class PF,PB prejanus
    class FDB,PDB,R,U data
    class S,AV,SU ext
```

Azul é o `forms`, roxo o prejanus, amarelo é onde os dados ficam e verde são os serviços
externos.

- **forms**: formulários de candidatura, cartas de recomendação e anexos. Os e-mails passam
  por uma fila no Redis, e o `celery-worker` os envia e apaga, a cada hora, os uploads que
  ficaram sem uso.
- **prejanus**: lista e detalhe das inscrições, comentários, rótulos e notas privadas. O
  `prejanus-back` tem banco próprio e um usuário só de leitura no banco do `forms`. Essa
  leitura direta é o único acoplamento entre os dois sistemas, junto com a pasta de uploads.
- **Postgres**: um único contêiner com os dois bancos, criados por
  `docker/init.postgres.sh`.

## O que o piloto reconstrói

O piloto serve para ver se reconstruir o caronte com o harness escala. Ele reconstrói só a
consulta do `prejanus-back`: o docente encontra uma inscrição, lê as respostas e abre os
anexos. Se o resultado parecer razoável, o experimento passa para o sistema inteiro.

```mermaid
flowchart LR
    T([Suíte HTTP<br/>como docente]) -->|"PIL-DOC-01..03"| PB["prejanus-back<br/>FastAPI · reconstruído"]
    PB -.->|"login · PIL-AUT-01"| SU{{"Senha Única USP<br/>DEV_USER_ID no teste"}}
    PB --> PDB[("banco do prejanus")]
    PB -.->|leitura| FDB[("banco do forms")]
    PB --> U[/uploads compartilhados/]
    FX[("fixture<br/>inscrição pronta + 8 PDFs")] --> PDB
    FX --> FDB
    FX --> U

    classDef test fill:#94a3b8,stroke:#334155,color:#0f172a
    classDef prejanus fill:#a78bfa,stroke:#5b21b6,color:#0f172a
    classDef data fill:#fbbf24,stroke:#92400e,color:#0f172a
    classDef ext fill:#4ade80,stroke:#166534,color:#0f172a
    class T test
    class PB prejanus
    class PDB,FDB,U,FX data
    class SU ext
```

A fixture monta o estado inicial igual no original e nas reconstruções, já com a inscrição
criada. Ficam de fora o `forms`, o `prejanus-front`, Redis, smtp4dev, ClamAV e as rotas do
`prejanus-back` que mandam e-mail.
