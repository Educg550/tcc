## Regras de Cypress

### Estrutura
- Testes independentes e executáveis isolados. Nenhum teste depende do estado de outro.
- Setup repetido vai para `beforeEach()`.
- Prefira poucos testes com várias asserções a muitos testes minúsculos.
- Asserções explícitas, sempre.

### Identificação de elementos

**Você não pode alterar o código**, só escrever specs. Então olhe o HTML que recebeu e use
o seletor mais estável que a aplicação **de fato** oferece, nesta ordem:

1. Atributo dedicado que já exista no HTML - `data-cy`, `data-testid`, `data-campo`, ou
   qualquer outro que nomeie o campo. Se existir, é a primeira escolha: procure por ele
   antes de qualquer outra coisa.
2. `id` ou `name` que já existam.
3. Texto visível, com `cy.contains()`.
4. Estrutura, em último caso.

**Cuidado com `cy.contains()` e regex ancorado.** O `cy.contains` casa contra o texto
inteiro do elemento, com espaço em branco e texto de filhos incluídos. Num rótulo que
envolve o campo, como `<label>NÚMERO <input></label>`, o texto é `"NÚMERO\n        "` e
`/^NÚMERO$/` **não casa**. Se precisar desambiguar rótulo que é prefixo de outro
(`NÚMERO` vs `NÚMERO DA AGÊNCIA`), use um atributo do item 1 em vez de âncora de regex.

### Espera
- Nunca use espera arbitrária: nada de `cy.wait(5000)`.
- Use as novas tentativas implícitas do Cypress, asserções que repetem sozinhas, e
  `timeout` maior na asserção quando o passo for genuinamente lento.
- Para esperar uma requisição, `cy.intercept()` com `cy.wait('@alias')`.

### Assincronismo
O Cypress tem fila de comandos e não é baseado em Promise. Misturar `async`/`await` ou
Promise com comandos `cy` gera instabilidade e erros como "returned a promise while also
invoking cy commands". Fique dentro das cadeias `cy`.

Nunca atribua resultado de comando `cy` a variável: use `.then()` ou `.as()`.

### Estilo
- Título do `it()` descreve comportamento do usuário e resultado esperado, em linguagem
  comum, sem detalhe de implementação.
- Determinístico e estável: o mesmo spec, contra o mesmo app, dá sempre o mesmo veredito.
  É isso que justifica esta suíte existir.
