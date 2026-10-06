describe("C2", () => {
  it("mostra as abas, seções e botão de envio na página inicial", () => {
    cy.visit("/");
    cy.get(".aba-btn").eq(0).should("contain.text", "ALUNOS").and("have.class", "ativa");
    cy.get(".aba-btn").eq(1).should("contain.text", "DOCENTES");
    cy.contains("legend", "SOLICITANTE E EVENTO").should("be.visible");
    cy.contains("legend", "ENDEREÇO DO SOLICITANTE").should("be.visible");
    cy.contains("legend", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO").should("be.visible");
    cy.contains("button", "Enviar solicitação").should("be.visible");
  });
});
