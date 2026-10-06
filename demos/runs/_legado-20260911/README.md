# Runs legadas — arquivadas em 2026-09-11

Execuções anteriores à remoção do modo `edicao`. Os `RUN.log` daqui seguem o schema
antigo: campo `modo` (`criacao`/`edicao`) em vez de `grupo` (`tdd`/`baseline`), e um bloco
`regressao` que não existe mais. Comparar número daqui com run nova exige traduzir as
chaves.

`piloto/_harness/RELATORIO.md` é a execução piloto de 2026-08-26 — o pytest passou 10/10 e
o CUA reprovou o C2 por falta de JavaScript. É a evidência que justifica o CUA no pipeline;
não descartar.
