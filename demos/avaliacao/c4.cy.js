import { aba, campo } from "./campos.js";

describe("C4", () => {
  it("trocar de aba e voltar não apaga o preenchimento", () => {
    cy.visit("/");
    campo("NOME COMPLETO - SEM ABREVIAR").type("João Souza");
    campo("PROGRAMA").type("Matemática Aplicada");
    aba("DOCENTES").click();
    campo("NOME COMPLETO - SEM ABREVIAR").type("Maria Silva");
    aba("ALUNOS").click();
    campo("NOME COMPLETO - SEM ABREVIAR").should("have.value", "João Souza");
    campo("PROGRAMA").should("have.value", "Matemática Aplicada");
  });
});
