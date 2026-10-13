---
slug: veredito
title: "Veredito entre as finalistas"
authors: [eduardo]
tags: [tcc, experimento]
---

Das duas finalistas do torneio, a vencedora é a `deepseek/run44/baseline`. 

<!-- truncate -->

## Torneio

A run44 ganhou o torneio cego e eliminou a run35 em confronto direto, na rodada de 32. A run35
ficou em segundo porque voltou pela repescagem ([post do desempatador](/blog/desempatador)).

## Nielsen

As notas são rótulos ordenados (Péssimo, Ruim, Regular, Bom, Excelente), sem distância
definida entre eles, então não tirei média. Comparei as duas runs heurística por
heurística, contando em quantas cada uma recebeu o rótulo mais alto de cada avaliador. As
notas estão no [post dos resultados](/blog/resultados-nielsen).

| Avaliador | run44 melhor | run35 melhor | Empate |
|---|---|---|---|
| Eduardo | 2 (heurísticas 3 e 4) | 0 | 8 |
| CUA | 0 | 2 (heurísticas 2 e 5) | 8 |

Eu ponho a run44 na frente em duas heurísticas, o CUA põe a run35 em outras duas, e o
resto empata. Na prática, a avaliação Nielsen não separa as duas.

## Abas e seções

Meu critério de desempate é a visibilidade: saber em que aba estou e onde começa cada
seção do formulário. São dois dos critérios que usei no torneio. Na run44, a aba ativa
tem um detalhe laranja no topo, e cada seção tem uma linha azul vertical à esquerda.

![Run44: a aba ativa com o detalhe laranja e a seção marcada pela linha azul vertical.](./run44.png)

Na run35, as duas abas são azuis e a ativa só fica mais escura. As seções são caixas com
o título na borda, sem marca lateral.

![Run35: abas no mesmo tom de azul e seções em caixas com o título na borda.](./run35.png)

No mesmo navegador e com o mesmo zoom, a fonte da run35 também é menor. Conferi no
`style.css` de cada uma: tirando as abas, todo texto da run35 é de 0,5 a 3 px menor.

| Elemento | run44 | run35 |
|---|---:|---:|
| Texto base da página | 13 px | 11 px |
| Nome da universidade | 22 px | 19 px |
| Nome do programa | 12 px | 11 px |
| Abas | 12 px | 12 px |
| Título da seção | 11 px | 10 px |
| Rótulo do campo | 10 px | 9 px |
| Texto digitado nos campos | 12,5 px | 11 px |
| Botão de envio | 13 px | 12 px |
| Mensagens de erro | 12,5 px | 11 px |
| Título da confirmação | 20 px | 18 px |
| Ofício | 12,5 px | 12 px |

## O campo de valor

Há ainda o campo de valor. Nas duas, a máscara trata os dígitos como
centavos: `150000` vira `R$ 1.500,00`. O placeholder da run44 é `150000`, coerente com a
máscara. O da run35 é `1500`, e quem digita o exemplo recebe `R$ 15,00`.

Os defeitos da run44 ficam na aparência e no texto: o botão de envio pede rolagem, e o
exemplo de CPF vem sem a pontuação que o rótulo pede, embora a máscara formate o CPF de
qualquer jeito.
