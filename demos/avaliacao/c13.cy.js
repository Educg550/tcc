import { enviar, naoTemTexto, preencher, temTexto } from "./campos.js";

describe("C13", () => {
  it("CPF com dígito verificador errado é recusado", () => {
    cy.visit("/");
    preencher({
      "DATA DE NASCIMENTO": "01021980",
      "CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678900",
    });
    enviar();
    naoTemTexto(/Solicitação registrada/);
    temTexto(/CPF inválido/);
  });
});
