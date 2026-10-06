import { enviar, preencher, temTexto } from "./campos.js";

// O ofício inteiro do requisito, não só as quatro linhas que C10 confere.
const LINHAS = [
  "E-mail:", "Dados do evento", "Evento:", "Período:", "Local:",
  "Apresentação de trabalho:", "Detalhamento:", "Endereço da(o) interessada(o)",
  "CEP:", "Dados para pagamento", "Data de nascimento:", "CPF:", "RG / RNM:",
  "Banco:", "Agência:", "Conta:",
  "Encaminhe-se ao Serviço Financeiro para providências.",
];

describe("E9", () => {
  it("o ofício traz todas as seções e linhas do modelo", () => {
    cy.visit("/");
    preencher();
    enviar();
    temTexto(/Solicitação registrada/);
    LINHAS.forEach((l) => temTexto(l));
    temTexto("aprovou na data de hoje, a solicitação de auxílio financeiro para a");
  });
});
