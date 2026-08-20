## Estilo de código

Escreva o mínimo que resolve o problema. Nada especulativo.

- Nada além do que foi pedido: sem funcionalidade extra, sem flexibilidade ou
  configurabilidade não solicitada, sem tratamento de erro para cenário impossível.
- Sem abstração para código de uso único: nada de interface com uma implementação,
  fábrica para um produto, config para valor que nunca muda.
- Reuse o que já existe no projeto antes de reimplementar. Biblioteca padrão antes de
  dependência nova. Recurso nativo da plataforma antes de biblioteca.
- Uma linha antes de cinquenta. Deleção acima de adição. Código entediante acima de
  código esperto.
- Mudança cirúrgica: toque só no que a tarefa exige, sem reformatar nem refatorar o
  que está em volta.
- O que nunca se corta: validação de entrada em fronteira de confiança, tratamento de
  erro que evita perda de dados, segurança, acessibilidade básica, e o que foi pedido
  explicitamente.
