import { campo, enviar, naoTemTexto, temTexto } from "./campos.js";

describe("C9", () => {
  it("valor zero é recusado e não gera ofício", () => {
    cy.visit("/");
    campo("VALOR SOLICITADO (R$)").clear().type("0");
    enviar();
    temTexto(/Valor solicitado deve ser maior que 0/);
    naoTemTexto(/Solicitação registrada/);
  });
});
