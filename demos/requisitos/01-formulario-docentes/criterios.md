# Critérios de aceitação - requisito 01

## C1 - o formulário aparece
Abrir a página inicial.
Esperado: os sete campos aparecem com os rótulos exatos, cada um com um placeholder
visível que explica o que preencher, e há um botão `Enviar solicitação`.

## C2 - valor solicitado é formatado como moeda ao digitar
Digitar `1500` no campo `VALOR SOLICITADO` e sair do campo, sem enviar o formulário.
Esperado: o campo passa a mostrar `R$ 15,00`.

## C3 - solicitação válida gera o ofício
Preencher: nome `Maria Silva`, N. USP `1234567`, programa `Ciência da Computação`,
evento `SBES 2026`, período `10 a 14 de setembro`, cidade `Porto Alegre`,
valor `150000`. Clicar em `Enviar solicitação`.
Esperado: a página mostra `Solicitação registrada` e o ofício contém `Maria Silva`,
`1234567` e `R$ 1.500,00`, sem nenhum marcador `<<...>>` sobrando.

## C4 - campo obrigatório vazio é barrado
Deixar o nome em branco, preencher o resto e enviar.
Esperado: a mensagem `Preencha todos os campos` aparece e o ofício não é gerado.

## C5 - N. USP não numérico é barrado
Preencher tudo, com N. USP `abc123`, e enviar.
Esperado: a mensagem `N. USP deve conter apenas números` aparece.

## C6 - valor solicitado zerado é barrado
Preencher tudo, com `VALOR SOLICITADO` igual a `0`, e enviar.
Esperado: a mensagem `Valor solicitado deve ser maior que 0` aparece e o ofício não é
gerado.
