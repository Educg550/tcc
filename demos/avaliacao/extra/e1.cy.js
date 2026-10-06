import { campo } from "./campos.js";

describe("E1", () => {
  it("máscara de CEP", () => {
    cy.visit("/");
    campo("CEP").clear().type("05508090").blur();
    campo("CEP").should("have.value", "05508-090");
  });
});
