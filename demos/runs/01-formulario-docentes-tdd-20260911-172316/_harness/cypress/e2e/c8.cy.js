describe("C8", () => {
  it("valida que N. USP contém apenas números", () => {
    cy.visit("/");
    cy.get('#form-alunos [data-campo="N. USP"]').type("abc123");
    cy.contains("#form-alunos button", "Enviar solicitação").click();
    cy.get("#form-alunos .erros").should("contain", "N. USP deve conter apenas números");
    cy.get("#confirmacao").should("be.hidden");
  });
});
