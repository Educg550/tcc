# Requisito 01: formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP

Aplicação web que substitui os dois Google Forms de solicitação de auxílio financeiro da
Pós-Graduação do IME-USP: o de **docentes** e o de **alunos**. Os dois convivem na mesma
página, em abas. O solicitante escolhe a aba, preenche seus dados, os dados do evento, o
endereço e os dados bancários; ao enviar, recebe de volta o ofício de solicitação já
redigido com os dados no lugar dos marcadores, pronto para encaminhar à CCP do programa.

## Tela única com duas abas

Cabeçalho institucional da USP no topo (ver **Aparência**) e, abaixo dele, duas abas com
os rótulos exatos `DOCENTES` e `ALUNOS`. A aba `DOCENTES` está ativa quando a página
abre. Clicar numa aba mostra o formulário dela e esconde o da outra, sem recarregar a
página e sem perder o que já foi digitado na aba que saiu de vista. A aba ativa é
visualmente distinguível da inativa.

Cada aba tem seu próprio formulário e seu próprio botão `Enviar solicitação` ao fim.

## Campos das duas abas

Os campos vêm em três blocos, cada um com seu título visível. Rótulos exatos, na ordem
abaixo. Todos obrigatórios, exceto os marcados como opcionais. As duas abas têm os mesmos
campos, com as duas exceções indicadas em `SOLICITANTE E EVENTO`.

### Bloco `SOLICITANTE E EVENTO`

- `NOME COMPLETO - SEM ABREVIAR` (texto)
- `N. USP` (só dígitos)
- `PROGRAMA` (texto)
- `NÍVEL` (**só na aba `ALUNOS`** — seleção entre `Mestrado` e `Doutorado`)
- `TIPO DE AUXÍLIO` (**só na aba `ALUNOS`** — seleção entre `Participação em evento`,
  `Banca de exame ou defesa` e `Outro`)
- `E-MAIL` (e-mail)
- `NOME DO EVENTO / BANCA DE EXAME OU DEFESA` (texto)
- `PERÍODO DO EVENTO, EXAME OU DEFESA` (texto)
- `CIDADE DO EVENTO, EXAME OU DEFESA` (texto)
- `ESTADO DO EVENTO, EXAME OU DEFESA` (texto)
- `PAÍS DO EVENTO, EXAME OU DEFESA` (texto)
- `LINK DO EVENTO, EXAME OU DEFESA` (texto, **opcional**)
- `VALOR SOLICITADO (R$)` (número natural maior que 0, formatado como moeda brasileira
  enquanto se digita — ver abaixo)
- `DETALHAMENTO DO PEDIDO` (texto longo, várias linhas)
- `IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?` (seleção entre `Pôster`,
  `Apresentação oral`, `Outra` e `Não irá apresentar trabalho`)

### Bloco `ENDEREÇO DO SOLICITANTE`

- `DATA DE NASCIMENTO` (data no formato `dd/mm/aaaa`, formatada enquanto se digita)
- `LOGRADOURO` (texto)
- `NÚMERO` (texto)
- `COMPLEMENTO` (texto, **opcional**)
- `BAIRRO` (texto)
- `CEP` (formato `00000-000`, formatado enquanto se digita)
- `CIDADE` (texto)
- `ESTADO` (texto)

### Bloco `INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO`

- `CPF (SEPARADOS POR PONTOS E TRAÇO)` (formato `000.000.000-00`, formatado enquanto se
  digita)
- `RG / RNM (SEPARADOS POR PONTOS E TRAÇO)` (texto)
- `NOME DO BANCO` (texto)
- `NÚMERO DA AGÊNCIA` (só dígitos)
- `NÚMERO DA CONTA` (texto)

## Campos que se formatam sozinhos

Quatro campos reformatam o que foi digitado no momento em que o usuário sai deles, sem
enviar o formulário. O usuário digita apenas dígitos; a pontuação é da aplicação.

`VALOR SOLICITADO (R$)` — os dígitos digitados são os centavos do valor, e o campo passa
a mostrar o valor em moeda brasileira, com ponto separando milhar e vírgula separando os
centavos:

| digitado | mostrado |
|---|---|
| `1500` | `R$ 15,00` |
| `150000` | `R$ 1.500,00` |
| `150000000` | `R$ 1.500.000,00` |

`CPF (SEPARADOS POR PONTOS E TRAÇO)` — digitar `12345678901` mostra `123.456.789-01`.

`CEP` — digitar `05508090` mostra `05508-090`.

`DATA DE NASCIMENTO` — digitar `01021980` mostra `01/02/1980`.

## Validação

Vale igual nas duas abas. Ao enviar, a página volta com a mesma aba ativa, os valores já
digitados preservados nos campos e, no topo do formulário daquela aba, **todas** as
mensagens de erro que se aplicam, uma por linha:

- Qualquer campo obrigatório vazio: `Preencha todos os campos` (uma única vez, não uma
  por campo).
- `N. USP` que não seja só dígitos: `N. USP deve conter apenas números`.
- `NÚMERO DA AGÊNCIA` que não seja só dígitos: `Número da agência deve conter apenas números`.
- `VALOR SOLICITADO (R$)` que não seja um número natural maior que 0:
  `Valor solicitado deve ser maior que 0`.
- `E-MAIL` sem `@` ou sem domínio: `E-mail inválido`.
- `CPF (SEPARADOS POR PONTOS E TRAÇO)` fora de `000.000.000-00`:
  `CPF deve estar no formato 000.000.000-00`.
- `CEP` fora de `00000-000`: `CEP deve estar no formato 00000-000`.
- `DATA DE NASCIMENTO` fora de `dd/mm/aaaa`:
  `Data de nascimento deve estar no formato dd/mm/aaaa`.

Enquanto houver erro, o ofício não é gerado.

Todo campo tem um placeholder visível, curto e autoexplicativo, com um exemplo de
preenchimento — nunca a repetição do rótulo. Em `DETALHAMENTO DO PEDIDO` o placeholder
pede o valor de cada despesa separadamente, como em `Hospedagem e alimentação: R$
500,00 / Passagem: R$ 1.500,00 / Inscrição no evento: R$ 1.000,00`.

## Após o envio válido

Mostrar a página de confirmação, com o mesmo cabeçalho institucional, o título
`Solicitação registrada` e, abaixo, o ofício com os dados preenchidos no lugar dos
marcadores:

```
Interessada(o): <<NOME COMPLETO - SEM ABREVIAR>> - <<N. USP>>
E-mail: <<E-MAIL>>
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: <<PROGRAMA>>

A CCP-<<PROGRAMA>> aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: <<NOME DO EVENTO / BANCA DE EXAME OU DEFESA>>
Período: <<PERÍODO DO EVENTO, EXAME OU DEFESA>>
Local: <<CIDADE DO EVENTO, EXAME OU DEFESA>> - <<ESTADO DO EVENTO, EXAME OU DEFESA>> - <<PAÍS DO EVENTO, EXAME OU DEFESA>>
Link do evento: <<LINK DO EVENTO, EXAME OU DEFESA>>
Apresentação de trabalho: <<IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?>>
Valor solicitado: <<VALOR SOLICITADO (R$)>>
Detalhamento: <<DETALHAMENTO DO PEDIDO>>

Endereço da(o) interessada(o)
<<LOGRADOURO>>, <<NÚMERO>>
Complemento: <<COMPLEMENTO>>
CEP: <<CEP>>
<<BAIRRO>>, <<CIDADE>> - <<ESTADO>>

Dados para pagamento
Data de nascimento: <<DATA DE NASCIMENTO>>
CPF: <<CPF (SEPARADOS POR PONTOS E TRAÇO)>>
RG / RNM: <<RG / RNM (SEPARADOS POR PONTOS E TRAÇO)>>
Banco: <<NOME DO BANCO>>
Agência: <<NÚMERO DA AGÊNCIA>>
Conta: <<NÚMERO DA CONTA>>

Encaminhe-se ao Serviço Financeiro para providências.
```

O ofício da aba `ALUNOS` é o mesmo, com duas linhas diferentes:

```
Assunto: Solicitação de Auxílio Financeiro - <<TIPO DE AUXÍLIO>>
Programa: <<PROGRAMA>> - <<NÍVEL>>
```

`VALOR SOLICITADO (R$)` aparece no ofício já formatado, como `R$ 1.500,00`. Quando
`LINK DO EVENTO, EXAME OU DEFESA` ou `COMPLEMENTO` ficarem vazios, a linha
correspondente sai do ofício em vez de aparecer vazia.

Os rótulos e mensagens acima devem estar dispostos exatamente assim.

## Aparência

A tela é um documento institucional da Universidade de São Paulo, não uma página de
teste. Os campos são muitos: o que decide se a tela é usável é o agrupamento e o
espaçamento, não enfeite.

### Identificação visual da USP

A pasta `images/` já está na raiz do projeto, com três arquivos que a aplicação serve
como estáticos e usa como estão — não os edite, não os gere, não baixe nada da rede:

- `images/usp-brasao-colorido.png` — o brasão da USP em cores, na proporção retrato.
- `images/usp-brasao.png` — o mesmo brasão em traço preto sobre fundo transparente.
- `images/usp-logo.png` — a sigla `USP` no logotipo institucional, em traço preto sobre
  fundo transparente, na proporção paisagem.

Com eles:

- Faixa no topo da página, em azul-escuro institucional (por exemplo `#12325b`), da
  borda esquerda à direita. À esquerda dela, `images/usp-brasao-colorido.png` com cerca
  de 56px de altura, proporção preservada; ao lado, em duas linhas de texto claro,
  `Universidade de São Paulo` e `Instituto de Matemática e Estatística — Pós-Graduação`.
- Ainda na faixa, encostado à direita, `images/usp-logo.png` com cerca de 32px de altura
  — como o logotipo é traço preto, ele vai dentro de um bloco de fundo branco com um
  pouco de folga em volta, para ter contraste sobre o azul.
- Rodapé da página, com o texto em cinza e centralizado, em duas linhas:
  `Rua do Matão, 1010 | Cidade Universitária | São Paulo-SP | CEP 05508-090` e
  `cpg@ime.usp.br | www.ime.usp.br`.
- Toda imagem tem `alt` descritivo.

### Formulário

- Fundo da página num azul-acinzentado muito claro (por exemplo `#eeeef8`). Sobre ele,
  um cartão único centralizado, de largura máxima em torno de 860px, fundo branco, cantos
  arredondados e sombra suave.
- As abas `DOCENTES` e `ALUNOS` ficam no alto do cartão, lado a lado, como abas de
  verdade: a ativa com fundo branco e uma barra na cor de destaque, a inativa apagada.
- Cor de destaque, usada no botão, na aba ativa e no realce de foco dos campos: um
  azul-violeta (por exemplo `#5159b4`, a cor do formulário original).
- Os três blocos aparecem como seções com o título em maiúsculas, na cor de destaque,
  separados por uma linha divisória e com respiro vertical entre eles.
- Rótulo acima do campo, em tamanho menor e peso maior que o texto digitado. Campo
  obrigatório marcado com `*` ao lado do rótulo.
- Campos de texto ocupam a largura do bloco, com altura confortável ao clique, borda
  visível e destaque de foco. Os campos curtos — `N. USP`, `VALOR SOLICITADO (R$)`,
  `DATA DE NASCIMENTO`, `NÚMERO`, `CEP`, `ESTADO`, `CPF (SEPARADOS POR PONTOS E TRAÇO)`,
  `RG / RNM (SEPARADOS POR PONTOS E TRAÇO)`, `NÚMERO DA AGÊNCIA` e `NÚMERO DA CONTA` —
  ficam lado a lado, duas colunas por linha, e passam a uma coluna em tela estreita.
- As mensagens de erro aparecem juntas num bloco de destaque vermelho no topo do
  formulário, antes do primeiro bloco de campos.
- O botão `Enviar solicitação` fica ao fim do formulário, na cor de destaque, ocupando a
  largura do bloco.

### Página de confirmação

Mesmo fundo, mesmo cartão e mesmo rodapé. No lugar da faixa azul, o papel de ofício:
`images/usp-brasao.png` com cerca de 72px de altura, centralizado no alto do cartão, e
abaixo dele, também centrado, `Universidade de São Paulo` e
`Instituto de Matemática e Estatística — Pós-Graduação`, separados do resto por uma linha
divisória. O ofício vem num bloco de texto monoespaçado sobre fundo levemente
acinzentado, preservando as quebras de linha.

Todo o CSS e todo o JavaScript são escritos à mão e embutidos na própria página: sem
framework, sem CDN, sem fonte remota e sem nenhum arquivo baixado da rede. A tipografia é
a pilha de fontes do sistema. As únicas imagens da aplicação são as três de `images/`.
