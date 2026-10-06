import { enviar, naoTemTexto, preencher, temTexto } from "./campos.js";

describe("C12", () => {
  it("data de nascimento inexistente é recusada", () => {
    cy.visit("/");
    preencher({
      "CPF (SEPARADOS POR PONTOS E TRAÇO)": "52998224725",
      "DATA DE NASCIMENTO": "32121990",
    });
    enviar();
    naoTemTexto(/Solicitação registrada/);
    temTexto(/Data de nascimento inválida/);
  });
});
