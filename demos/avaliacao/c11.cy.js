import { aba, enviar, preencher, temTexto } from "./campos.js";

describe("C11", () => {
  it("aba DOCENTES completa gera o ofício de verba do programa", () => {
    cy.visit("/");
    aba("DOCENTES").click();
    preencher({
      "NOME COMPLETO - SEM ABREVIAR": "Maria Silva",
      "N. USP": "1234567",
      "PROGRAMA": "Ciência da Computação",
      "VALOR SOLICITADO (R$)": "150000",
      "CPF (SEPARADOS POR PONTOS E TRAÇO)": "12345678909",
    });
    enviar();
    temTexto(/Solicitação registrada/);
    temTexto("Interessada(o): Maria Silva - 1234567");
    temTexto("Assunto: Solicitação de Auxílio Financeiro - Verba do programa");
    temTexto("Programa: Ciência da Computação");
    temTexto("Valor solicitado: R$ 1.500,00");
    temTexto("CPF: 123.456.789-09");
    cy.get("body").should("not.contain.text", "<<");
  });
});
