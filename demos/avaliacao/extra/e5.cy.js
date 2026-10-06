import { campo, enviar, preencher, temTexto } from "./campos.js";

// O requisito manda mostrar **todas** as mensagens que se aplicam, uma por linha, e não
// parar na primeira: e um formulario cheio isola essa regra da validacao de obrigatorios.
describe("E5", () => {
  it("mostra todas as mensagens que se aplicam, não só a primeira", () => {
    cy.visit("/");
    preencher();
    campo("N. USP").clear().type("abc").blur();
    campo("NÚMERO DA AGÊNCIA").clear().type("xyz").blur();
    campo("E-MAIL").clear().type("joao@").blur();
    enviar();
    temTexto(/N\. USP deve conter apenas números/);
    temTexto(/Número da agência deve conter apenas números/);
    temTexto(/E-mail inválido/);
  });
});
