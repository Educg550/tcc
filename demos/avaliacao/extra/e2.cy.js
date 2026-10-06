import { campo } from "./campos.js";

describe("E2", () => {
  it("máscara de data de nascimento", () => {
    cy.visit("/");
    campo("DATA DE NASCIMENTO").clear().type("01021980").blur();
    campo("DATA DE NASCIMENTO").should("have.value", "01/02/1980");
  });
});
