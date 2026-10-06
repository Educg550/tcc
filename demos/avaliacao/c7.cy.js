import { enviar, naoTemTexto, temTexto } from "./campos.js";

describe("C7", () => {
  it("formulário vazio pede o preenchimento e não gera ofício", () => {
    cy.visit("/");
    enviar();
    temTexto(/Preencha todos os campos/);
    naoTemTexto(/Solicitação registrada/);
  });
});
