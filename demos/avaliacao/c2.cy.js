import { aba, temTexto } from "./campos.js";

describe("C2", () => {
  it("abas, seções e botão de envio na página inicial", () => {
    cy.visit("/");
    aba("ALUNOS").should("exist");
    aba("DOCENTES").should("exist");
    temTexto(/SOLICITANTE E EVENTO/);
    temTexto(/ENDEREÇO DO SOLICITANTE/);
    temTexto(/INFORMAÇÕES PARA PAGAMENTO \/ REEMBOLSO/);
    temTexto(/Enviar solicita/i);
    // ALUNOS ativa quando abre: os campos exclusivos dela estão na tela.
    temTexto(/NÍVEL/);
    temTexto(/TIPO DE AUXÍLIO/);
  });
});
