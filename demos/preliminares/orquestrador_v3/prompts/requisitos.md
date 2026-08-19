# Requisito: TODO list web (CRUD)

Implemente uma aplicação web de lista de tarefas em HTML/CSS/JS puro: sem
frameworks, sem build, sem CDN, sem dependências externas. Single-page com três
arquivos: `index.html`, `style.css`, `app.js`. Persistência no `localStorage`.

## Funcionalidades

1. Adicionar tarefa: um campo de texto com placeholder `Nova tarefa` e um botão
   `Adicionar`. Submeter cria a tarefa na lista de pendentes.
2. Listar tarefas: as pendentes aparecem por padrão; cada item mostra o título e
   suas ações.
3. Concluir tarefa: um botão `Concluir` em cada item marca a tarefa como concluída.
4. Editar tarefa: um botão `Editar` permite alterar o título da tarefa.
5. Remover tarefa: um botão `Remover` exclui a tarefa.
6. Filtrar: botões `Pendentes`, `Concluídas` e `Todas` alternam o que é exibido.

## Restrições de UI (contratos visíveis)

- Use exatamente os rótulos/textos acima (`Nova tarefa`, `Adicionar`, `Concluir`,
  `Editar`, `Remover`, `Pendentes`, `Concluídas`, `Todas`) para que sejam
  localizáveis por um testador automatizado.
- Tudo nativo: nada de libs externas.
