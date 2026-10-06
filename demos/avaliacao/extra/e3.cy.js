import { campo, enviar, naoTemTexto, preencher, temTexto } from "./campos.js";

describe("E3", () => {
  it("agência não numérica é recusada com a mensagem exata", () => {
    cy.visit("/");
    preencher();
    campo("NÚMERO DA AGÊNCIA").clear().type("abc123").blur();
    enviar();
    temTexto(/Número da agência deve conter apenas números/);
    naoTemTexto(/Solicitação registrada/);
  });
});
