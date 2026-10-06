describe("C12", () => {
  it("rejeita data de nascimento inválida", () => {
    cy.visit("/");

    cy.get('#form-alunos [data-campo="NOME COMPLETO - SEM ABREVIAR"]').type("João Souza");
    cy.get('#form-alunos [data-campo="N. USP"]').type("7654321");
    cy.get('#form-alunos [data-campo="PROGRAMA"]').type("Matemática Aplicada");
    cy.get('#form-alunos [data-campo="NÍVEL"]').select("Mestrado");
    cy.get('#form-alunos [data-campo="TIPO DE AUXÍLIO"]').select("Participação em evento");
    cy.get('#form-alunos [data-campo="E-MAIL"]').type("joao.souza@usp.br");
    cy.get('#form-alunos [data-campo="NOME DO EVENTO / BANCA DE EXAME OU DEFESA"]').type("Congresso Brasileiro de Matemática");
    cy.get('#form-alunos [data-campo="PERÍODO DO EVENTO, EXAME OU DEFESA"]').type("10/03/2025 a 12/03/2025");
    cy.get('#form-alunos [data-campo="CIDADE DO EVENTO, EXAME OU DEFESA"]').type("Belo Horizonte");
    cy.get('#form-alunos [data-campo="ESTADO DO EVENTO, EXAME OU DEFESA"]').type("MG");
    cy.get('#form-alunos [data-campo="PAÍS DO EVENTO, EXAME OU DEFESA"]').type("Brasil");
    cy.get('#form-alunos [data-campo="VALOR SOLICITADO (R$)"]').type("150000");
    cy.get('#form-alunos [data-campo="IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"]').select("Pôster");
    cy.get('#form-alunos [data-campo="DETALHAMENTO DO PEDIDO"]').type("Solicito auxílio para participação no evento.");
    cy.get('#form-alunos [data-campo="DATA DE NASCIMENTO"]').type("32121990");
    cy.get('#form-alunos [data-campo="LOGRADOURO"]').type("Rua Teste");
    cy.get('#form-alunos [data-campo="NÚMERO"]').type("100");
    cy.get('#form-alunos [data-campo="BAIRRO"]').type("Butantã");
    cy.get('#form-alunos [data-campo="CEP"]').type("05508090");
    cy.get('#form-alunos [data-campo="CIDADE"]').type("São Paulo");
    cy.get('#form-alunos [data-campo="ESTADO"]').type("SP");
    cy.get('#form-alunos [data-campo="CPF (SEPARADOS POR PONTOS E TRAÇO)"]').type("52998224725");
    cy.get('#form-alunos [data-campo="RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"]').type("12.345.678-9");
    cy.get('#form-alunos [data-campo="NOME DO BANCO"]').type("Banco do Brasil");
    cy.get('#form-alunos [data-campo="NÚMERO DA AGÊNCIA"]').type("1234");
    cy.get('#form-alunos [data-campo="NÚMERO DA CONTA"]').type("12345-6");

    cy.contains("#form-alunos button", "Enviar solicitação").click();

    cy.get("#form-alunos .erros").should("contain", "Data de nascimento inválida");
    cy.get("#confirmacao").should("be.hidden");
  });
});
