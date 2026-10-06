describe("C5", () => {
  it("formata o valor solicitado em reais ao sair do campo", () => {
    cy.visit("/");
    cy.get('#form-alunos [data-campo="VALOR SOLICITADO (R$)"]')
      .type("1500")
      .blur()
      .should("have.value", "R$ 15,00");

    cy.get('#form-alunos [data-campo="VALOR SOLICITADO (R$)"]')
      .clear()
      .type("150000000")
      .blur()
      .should("have.value", "R$ 1.500.000,00");
  });
});
