import { aba, temTexto, naoTemTexto } from "./campos.js";

// Os rótulos exatos do requisito, na ordem dos três blocos.
const COMUNS = [
  "NOME COMPLETO - SEM ABREVIAR", "N. USP", "PROGRAMA", "E-MAIL",
  "NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "PERÍODO DO EVENTO, EXAME OU DEFESA",
  "CIDADE DO EVENTO, EXAME OU DEFESA", "ESTADO DO EVENTO, EXAME OU DEFESA",
  "PAÍS DO EVENTO, EXAME OU DEFESA", "LINK DO EVENTO, EXAME OU DEFESA",
  "VALOR SOLICITADO (R$)", "DETALHAMENTO DO PEDIDO",
  "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "DATA DE NASCIMENTO", "LOGRADOURO",
  "NÚMERO", "COMPLEMENTO", "BAIRRO", "CEP", "CIDADE", "ESTADO",
  "CPF (SEPARADOS POR PONTOS E TRAÇO)", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
  "NOME DO BANCO", "NÚMERO DA AGÊNCIA", "NÚMERO DA CONTA",
];
const SO_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"];

describe("E8", () => {
  it("as duas abas têm os rótulos exatos, e NÍVEL e TIPO DE AUXÍLIO só em ALUNOS", () => {
    cy.visit("/");
    [...COMUNS, ...SO_ALUNOS].forEach((r) => temTexto(r));
    aba("DOCENTES").click();
    COMUNS.forEach((r) => temTexto(r));
    SO_ALUNOS.forEach((r) => naoTemTexto(r));
  });
});
