describe("C11", () => {
  it("registra a solicitação de docente e gera o ofício correto", () => {
    cy.visit("/");
    cy.contains(".aba-btn", "DOCENTES").click();

    cy.get('#form-docentes [data-campo="NOME COMPLETO - SEM ABREVIAR"]').type("Maria Silva");
    cy.get('#form-docentes [data-campo="N. USP"]').type("1234567");
    cy.get('#form-docentes [data-campo="PROGRAMA"]').type("Ciência da Computação");
    cy.get('#form-docentes [data-campo="E-MAIL"]').type("maria.silva@usp.br");
    cy.get('#form-docentes [data-campo="NOME DO EVENTO / BANCA DE EXAME OU DEFESA"]').type("Congresso Brasileiro de Computação");
    cy.get('#form-docentes [data-campo="PERÍODO DO EVENTO, EXAME OU DEFESA"]').type("10/03/2025 a 12/03/2025");
    cy.get('#form-docentes [data-campo="CIDADE DO EVENTO, EXAME OU DEFESA"]').type("Belo Horizonte");
    cy.get('#form-docentes [data-campo="ESTADO DO EVENTO, EXAME OU DEFESA"]').type("MG");
    cy.get('#form-docentes [data-campo="PAÍS DO EVENTO, EXAME OU DEFESA"]').type("Brasil");
    cy.get('#form-docentes [data-campo="VALOR SOLICITADO (R$)"]').type("150000");
    cy.get('#form-docentes [data-campo="IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"]').select("Pôster");
    cy.get('#form-docentes [data-campo="DETALHAMENTO DO PEDIDO"]').type("Solicito auxílio para participação no evento.");
    cy.get('#form-docentes [data-campo="DATA DE NASCIMENTO"]').type("01021980");
    cy.get('#form-docentes [data-campo="LOGRADOURO"]').type("Rua Teste");
    cy.get('#form-docentes [data-campo="NÚMERO"]').type("100");
    cy.get('#form-docentes [data-campo="BAIRRO"]').type("Butantã");
    cy.get('#form-docentes [data-campo="CEP"]').type("05508090");
    cy.get('#form-docentes [data-campo="CIDADE"]').type("São Paulo");
    cy.get('#form-docentes [data-campo="ESTADO"]').type("SP");
    cy.get('#form-docentes [data-campo="CPF (SEPARADOS POR PONTOS E TRAÇO)"]').type("12345678909");
    cy.get('#form-docentes [data-campo="RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"]').type("12.345.678-9");
    cy.get('#form-docentes [data-campo="NOME DO BANCO"]').type("Banco do Brasil");
    cy.get('#form-docentes [data-campo="NÚMERO DA AGÊNCIA"]').type("1234");
    cy.get('#form-docentes [data-campo="NÚMERO DA CONTA"]').type("12345-6");

    cy.contains("#form-docentes button", "Enviar solicitação").click();

    cy.contains("h2", "Solicitação registrada").should("be.visible");
    cy.get("#oficio").should("contain", "Interessada(o): Maria Silva - 1234567");
    cy.get("#oficio").should("contain", "Assunto: Solicitação de Auxílio Financeiro - Verba do programa");
    cy.get("#oficio").should("contain", "Programa: Ciência da Computação");
    cy.get("#oficio").should("contain", "Valor solicitado: R$ 1.500,00");
    cy.get("#oficio").should("contain", "CPF: 123.456.789-09");
    cy.get("#oficio").invoke("text").should("not.match", /<<.*?>>/);
  });
});
