import { campo, enviar, naoTemTexto, preencher, temTexto } from "./campos.js";

describe("E4", () => {
  it("e-mail sem domínio é recusado com a mensagem exata", () => {
    cy.visit("/");
    preencher();
    campo("E-MAIL").clear().type("joao@").blur();
    enviar();
    temTexto(/E-mail inválido/);
    naoTemTexto(/Solicitação registrada/);
  });
});
