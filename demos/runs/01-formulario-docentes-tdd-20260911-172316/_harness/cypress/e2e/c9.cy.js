describe("C9", () => {
  it("exige valor solicitado maior que zero", () => {
    cy.visit("/");
    cy.get('#form-alunos [data-campo="VALOR SOLICITADO (R$)"]').type("0");
    cy.contains("#form-alunos button", "Enviar solicitação").click();
    cy.get("#form-alunos .erros").should("contain", "Valor solicitado deve ser maior que 0");
    cy.get("#confirmacao").should("be.hidden");
  });
});
