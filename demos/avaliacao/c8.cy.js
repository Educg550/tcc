import { campo, enviar, temTexto } from "./campos.js";

describe("C8", () => {
  it("N. USP não numérico é recusado com a mensagem exata", () => {
    cy.visit("/");
    campo("N. USP").clear().type("abc123");
    enviar();
    temTexto(/N\. USP deve conter apenas números/);
  });
});
