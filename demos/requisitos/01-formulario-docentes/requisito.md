# Requisito 01: formulário de solicitação de auxílio para docentes

Aplicação web em Flask que substitui o Google Forms de solicitação de auxílio
financeiro para docentes do IME. A aplicação fica em `app.py` e respeita a variável
de ambiente `PORT`, com 5000 como padrão. Sem banco de dados: as solicitações ficam
em memória.

## Tela única com o formulário

Campos, todos obrigatórios, com estes rótulos exatos:

- `NOME COMPLETO - SEM ABREVIAR` (texto)
- `N. USP` (numérico)
- `PROGRAMA` (texto)
- `NOME DO EVENTO` (texto)
- `PERÍODO DO EVENTO` (texto)
- `CIDADE DO EVENTO` (texto)
- `VALOR SOLICITADO` (texto, aceita `R$ 1.500,00` ou `US$ 300.00`)

Um botão `Enviar solicitação`.

## Validação

- Campo obrigatório vazio: a página volta com a mensagem `Preencha todos os campos`.
- `N. USP` que não seja só dígitos: mensagem `N. USP deve conter apenas números`.

## Após o envio válido

Mostrar a página de confirmação com o título `Solicitação registrada` e, abaixo, o
ofício com os dados preenchidos no lugar dos marcadores:

```
Interessada(o): <<NOME COMPLETO - SEM ABREVIAR>> - <<N. USP>>
Assunto: Solicitação de Auxílio Financeiro
Programa: <<PROGRAMA>>
Evento: <<NOME DO EVENTO>>
Período: <<PERÍODO DO EVENTO>>
Local: <<CIDADE DO EVENTO>>
Valor solicitado: <<VALOR SOLICITADO>>
```

Os rótulos e mensagens acima são o contrato testável: use os textos exatamente assim.
