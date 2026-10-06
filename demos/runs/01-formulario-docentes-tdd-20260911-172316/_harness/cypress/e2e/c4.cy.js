describe("C4", () => {
  it("mantém o preenchimento da aba ALUNOS ao trocar de aba e voltar", () => {
    cy.visit("/");
    cy.get('#form-alunos [data-campo="NOME COMPLETO - SEM ABREVIAR"]').type("João Souza");
    cy.get('#form-alunos [data-campo="PROGRAMA"]').type("Matemática Aplicada");

    cy.contains(".aba-btn", "DOCENTES").click();
    cy.get('#form-docentes [data-campo="NOME COMPLETO - SEM ABREVIAR"]').type("Maria Silva");

    cy.contains(".aba-btn", "ALUNOS").click();

    cy.contains(".aba-btn", "ALUNOS").should("have.class", "ativa");
    cy.get('#form-alunos [data-campo="NOME COMPLETO - SEM ABREVIAR"]').should("have.value", "João Souza");
    cy.get('#form-alunos [data-campo="PROGRAMA"]').should("have.value", "Matemática Aplicada");
  });
});
