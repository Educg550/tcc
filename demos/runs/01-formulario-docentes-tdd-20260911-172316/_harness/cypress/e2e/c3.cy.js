describe("C3", () => {
  it("esconde os campos NÍVEL e TIPO DE AUXÍLIO na aba DOCENTES", () => {
    cy.visit("/");
    cy.get('#form-alunos [data-campo="NÍVEL"]').should("exist");
    cy.get('#form-alunos [data-campo="TIPO DE AUXÍLIO"]').should("exist");

    cy.contains(".aba-btn", "DOCENTES").click();

    cy.contains(".aba-btn", "DOCENTES").should("have.class", "ativa");
    cy.get("#form-docentes").should("have.class", "ativa");
    cy.get('#form-docentes [data-campo="NÍVEL"]').should("not.exist");
    cy.get('#form-docentes [data-campo="TIPO DE AUXÍLIO"]').should("not.exist");
    cy.get('#form-docentes [data-campo="NOME COMPLETO - SEM ABREVIAR"]').should("exist");
    cy.get('#form-docentes [data-campo="PROGRAMA"]').should("exist");
    cy.get('#form-docentes [data-campo="CPF (SEPARADOS POR PONTOS E TRAÇO)"]').should("exist");
  });
});
