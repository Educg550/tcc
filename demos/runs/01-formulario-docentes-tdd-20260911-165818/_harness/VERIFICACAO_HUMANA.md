# Verificação humana

Run: `01-formulario-docentes-tdd-20260911-165818` (grupo tdd, sonnet 5 nas duas etapas).
Estado do CI no momento da verificação: **27 passed / 0 failed**, `intacto: true`, CUA não
executado (`--sem-cua`).

Operador humano preencheu o formulário da aba `ALUNOS` no navegador e enviou. A submissão
foi **aceita** e produziu o ofício abaixo.

## Ofício gerado

```
Solicitação registrada

Interessada(o): 12313 - 1
E-mail: hahaha@email.com
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: 2 - Mestrado

A CCP-2 aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: 2123
Período: a
Local: 124124 - 123123 - 12312412
Link do evento: 45124123
Apresentação de trabalho: Não irá apresentar trabalho
Valor solicitado: R$ 1.239,51
Detalhamento: 3

Endereço da(o) interessada(o)
124124, rua bujão
CEP: 05360-150
a, 1 - 1

Dados para pagamento
Data de nascimento: 32/12/3923
CPF: 128.238.123-82
RG / RNM: a
Banco: 22112
Agência: 1
Conta: a

Encaminhe-se ao Serviço Financeiro para providências.
```

## O que passou

### Data impossível

`DATA DE NASCIMENTO` = `32/12/3923`. Dia 32; ano 3923.

O código gerado valida com uma expressão regular de forma, não de data:

```python
if not campo_vazio(data_nasc) and not re.match(r"^\d{2}/\d{2}/\d{4}$", str(data_nasc)):
    erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
```

O requisito declara o campo como `(data no formato dd/mm/aaaa, ...)` e a mensagem de erro
fala em `formato`. Leitura estrita da mensagem: `32/12/3923` está no formato. Leitura do
tipo declarado (`data`): não é uma data. É o candidato mais forte a defeito genuíno desta
run — e nenhuma das duas leituras é decidível só pelo texto do requisito.

### CPF sem dígito verificador

`128.238.123-82` respeita `000.000.000-00` e não é um CPF válido. O requisito só pede o
formato, então o código está em conformidade com o que foi escrito.

### Campos de texto com conteúdo arbitrário

`NOME COMPLETO - SEM ABREVIAR` = `12313`, `PROGRAMA` = `2`, `PERÍODO` = `a`,
`CIDADE`/`ESTADO` = `1`. `LOGRADOURO` = `124124` e `NÚMERO` = `rua bujão` estão
semanticamente trocados. Todos declarados como `texto`, sem restrição adicional: nenhuma
regra do requisito foi violada.

## Leitura

Tudo o que foi enviado satisfaz o requisito como ele está escrito hoje. A seção de
validação é inteiramente **sintática** — obrigatoriedade, "só dígitos", formatos de
máscara, e-mail com `@` e domínio — e nunca exige que o dado seja plausível.

Consequência para o experimento: o verde de 27/27 não é falso. Os testes cobrem as regras
que o requisito enuncia, e o código as implementa. O que falta está a montante, no próprio
requisito.

Isso limita o alcance do CUA como avaliador final. O `criterios.toml` é derivado do mesmo
requisito, e nenhum dos 11 critérios exerce data impossível ou CPF inválido — C11 usa
`12345678901`, que é bem-formado. O CUA detecta divergência entre requisito e
implementação; ele não detecta lacuna do requisito. Uma verificação humana exploratória,
como esta, detecta.
