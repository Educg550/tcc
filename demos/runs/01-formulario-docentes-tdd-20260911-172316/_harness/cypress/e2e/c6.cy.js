describe("C6", () => {
  it("formata o CPF ao sair do campo", () => {
    cy.visit("/");
    cy.get('#form-alunos [data-campo="CPF (SEPARADOS POR PONTOS E TRAÇO)"]')
      .type("12345678909")
      .blur()
      .should("have.value", "123.456.789-09");
  });
});
