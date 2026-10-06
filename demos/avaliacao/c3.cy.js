import { aba, naoTemTexto, temTexto } from "./campos.js";

describe("C3", () => {
  it("aba DOCENTES esconde NÍVEL e TIPO DE AUXÍLIO", () => {
    cy.visit("/");
    temTexto(/NÍVEL/);
    aba("DOCENTES").click();
    naoTemTexto(/NÍVEL/);
    naoTemTexto(/TIPO DE AUXÍLIO/);
    temTexto(/NOME COMPLETO - SEM ABREVIAR/);
  });
});
