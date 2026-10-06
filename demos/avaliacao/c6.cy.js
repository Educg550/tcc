import { campo } from "./campos.js";

describe("C6", () => {
  it("máscara de CPF", () => {
    cy.visit("/");
    campo("CPF (SEPARADOS POR PONTOS E TRAÇO)").clear().type("12345678909").blur();
    campo("CPF (SEPARADOS POR PONTOS E TRAÇO)").should("have.value", "123.456.789-09");
  });
});
