import { campo, enviar, naoTemTexto, preencher, temTexto } from "./campos.js";

describe("E10", () => {
  it("link e complemento vazios somem do ofício em vez de sair em branco", () => {
    cy.visit("/");
    preencher();
    campo("LINK DO EVENTO, EXAME OU DEFESA").clear();
    campo("COMPLEMENTO").clear();
    enviar();
    temTexto(/Solicitação registrada/);
    naoTemTexto("Link do evento:");
    naoTemTexto("Complemento:");
  });
});
