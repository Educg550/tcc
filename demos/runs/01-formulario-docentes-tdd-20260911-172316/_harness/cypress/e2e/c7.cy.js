describe("C7", () => {
  it("exige o preenchimento de todos os campos ao enviar em branco", () => {
    cy.visit("/");
    cy.contains("#form-alunos button", "Enviar solicitação").click();
    cy.get("#form-alunos .erros").should("contain", "Preencha todos os campos");
    cy.get("#confirmacao").should("be.hidden");
  });
});
