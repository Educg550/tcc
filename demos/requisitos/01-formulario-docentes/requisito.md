# Requisito 01: formulário de solicitação de auxílio para docentes

Aplicação web em FastAPI que substitui o Google Forms de solicitação de auxílio
financeiro para docentes do IME.

## Tela única com o formulário

Campos, todos obrigatórios:

- `NOME COMPLETO - SEM ABREVIAR` (texto)
- `N. USP` (número natural)
- `PROGRAMA` (texto)
- `NOME DO EVENTO` (texto)
- `PERÍODO DO EVENTO` (texto)
- `CIDADE DO EVENTO` (texto)
- `VALOR SOLICITADO` (número natural maior que 0, que é convertido para moeda brasileira, ex: digitar `1500` -> `R$ 15,00`, digitar `150000` -> `R$ 1.500,00`, digitar `150000000` -> `R$ 1.500.000,00`, etc.)
  - Ao terminar de digitar, deve formatar como `R$ 1.500,00` (com vírgula e ponto como separadores de milhar e decimal, respectivamente).

Um botão `Enviar solicitação`.

## Validação

- Campo obrigatório vazio: a página volta com a mensagem `Preencha todos os campos`.
- `N. USP` que não seja só dígitos: mensagem `N. USP deve conter apenas números`.
- Campo `VALOR SOLICITADO` que não seja um número natural maior que 0: mensagem `Valor solicitado deve ser maior que 0`.
- Placeholders visíveis, claros e autoexplicativos para cada campo.

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

Os rótulos e mensagens acima devem estar dispostos exatamente assim.
