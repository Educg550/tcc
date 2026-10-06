import { campo } from "./campos.js";

describe("C5", () => {
  it("máscara de moeda no VALOR SOLICITADO", () => {
    cy.visit("/");
    campo("VALOR SOLICITADO (R$)").clear().type("1500").blur();
    campo("VALOR SOLICITADO (R$)").should("have.value", "R$ 15,00");
    campo("VALOR SOLICITADO (R$)").clear().type("150000000").blur();
    campo("VALOR SOLICITADO (R$)").should("have.value", "R$ 1.500.000,00");
  });
});
