## Como a aplicação é executada

O harness inicia a aplicação com:

```
{comando_app}
```

E verifica com:

```
{comando_teste}
```

O ambiente é **Python {python}** e tem exatamente estes pacotes, mais a biblioteca padrão:

{pacotes}

Nada além disso está instalado. Importar qualquer outra coisa quebra na hora de rodar, e a
sintaxe tem que ser válida na versão de Python acima. Escreva a aplicação de modo que o
comando acima a inicie. Você não executa nenhum comando - quem executa é o harness.
