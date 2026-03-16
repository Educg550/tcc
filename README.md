# TCC — Eduardo Cruz Guedes

Site hub do TCC de Eduardo Cruz Guedes, NUSP 13672752, Bacharelado em Ciência da Computação (5º ano) — IME-USP.

**Orientadores:** Prof. Paulo Meirelles (IME-USP) · Prof. Jorge Melegati (INESC TEC / Universidade do Porto)

**Tema:** Avaliação de um Pipeline Multiagente Baseado em TDD com Validação Comportamental via Computer Using Agents.

Site publicado em: https://educg550.github.io/tcc/

---

## Desenvolvimento local

```bash
npm install
npm start       # dev server em localhost:3000
npm run build   # build de produção
npm run serve   # testar build localmente
```

## Deploy

Deploy automático via GitHub Actions a cada push na branch `main`. O workflow (`.github/workflows/deploy.yml`) publica o conteúdo no branch `gh-pages`.

GitHub Pages ativado via: **Settings → Pages → Source → branch `gh-pages`**.

## Estrutura

- `docs/` — documentação principal do TCC (proposta, metodologia, referências)
- `blog/` — diário de pesquisa
- `raw/` — materiais brutos (ignorado pelo git)
