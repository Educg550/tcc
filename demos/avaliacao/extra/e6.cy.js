import { aba, campo, enviar, naoTemTexto } from "./campos.js";

describe("E6", () => {
  it("erro preserva a aba ativa e o que já tinha sido digitado", () => {
    cy.visit("/");
    aba("DOCENTES").click();
    campo("NOME COMPLETO - SEM ABREVIAR").clear().type("Maria Silva");
    campo("N. USP").clear().type("abc");
    enviar();
    naoTemTexto(/Solicitação registrada/);
    // A mesma aba continua ativa: `NÍVEL` só existe em `ALUNOS`.
    naoTemTexto(/NÍVEL/);
    campo("NOME COMPLETO - SEM ABREVIAR").should("have.value", "Maria Silva");
  });
});
