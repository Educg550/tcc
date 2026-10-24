## Como a aplicação é executada

O harness inicia a aplicação com:

```
{comando_app}
```

E verifica com:

```
{comando_teste}
```

O ambiente Python é **Python {python}** e tem estes pacotes, mais a biblioteca padrão:

{pacotes}

Não importe pacotes Python fora dessa lista. A sintaxe tem que ser válida na versão de
Python acima. Outros runtimes e suas dependências, quando necessários, são declarados
no requisito. Escreva a aplicação de modo que o
comando acima a inicie. Você não executa nenhum comando - quem executa é o harness.
