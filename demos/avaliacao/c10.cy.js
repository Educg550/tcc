import { enviar, preencher, temTexto } from "./campos.js";

describe("C10", () => {
  it("aba ALUNOS completa gera o ofício com os dados no lugar", () => {
    cy.visit("/");
    preencher({
      "NOME COMPLETO - SEM ABREVIAR": "João Souza",
      "N. USP": "7654321",
      "PROGRAMA": "Matemática Aplicada",
      "NÍVEL": "Mestrado",
      "TIPO DE AUXÍLIO": "Participação em evento",
      "VALOR SOLICITADO (R$)": "150000",
      "CPF (SEPARADOS POR PONTOS E TRAÇO)": "52998224725",
      "DATA DE NASCIMENTO": "01021980",
    });
    enviar();
    temTexto(/Solicitação registrada/);
    temTexto("Interessada(o): João Souza - 7654321");
    temTexto("Assunto: Solicitação de Auxílio Financeiro - Participação em evento");
    temTexto("Programa: Matemática Aplicada - Mestrado");
    temTexto("Valor solicitado: R$ 1.500,00");
    cy.get("body").should("not.contain.text", "<<");
  });
});
