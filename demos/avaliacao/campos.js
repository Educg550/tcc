// Suíte única para todas as runs: só localiza pelo que o requisito fixa - o texto
// visível. Nada de classe, id ou atributo inventado por uma implementação, senão a
// régua muda de run para run e deixa de comparar.

const norma = (s) =>
  (s || "")
    .replace(/[ ​]/g, " ")
    .replace(/[‐-―−]/g, "-")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[*:\s]+$/, "")
    .toLocaleUpperCase("pt-BR");

const controles = "input:not([type=hidden]), select, textarea";

const regex = (alvo) =>
  alvo instanceof RegExp
    ? alvo
    : new RegExp(alvo.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

function acharControle(doc, alvo) {
  const achados = [];
  for (const rotulo of doc.querySelectorAll("label, legend")) {
    if (norma(rotulo.textContent) !== alvo) continue;
    const grupo = rotulo.closest("fieldset, .campo, div");
    const achado =
      (rotulo.htmlFor && doc.getElementById(rotulo.htmlFor)) ||
      rotulo.querySelector(controles) ||
      (grupo && grupo.querySelector(controles));
    if (achado) achados.push(achado);
  }
  for (const el of doc.querySelectorAll(controles)) {
    const casa = ["aria-label", "placeholder", "name", "id", "data-campo"].some(
      (a) => norma(el.getAttribute(a)) === alvo,
    );
    if (casa) achados.push(el);
  }
  // O mesmo rótulo existe duas vezes, uma por aba; a aba escondida não conta.
  return achados.find((el) => el.offsetParent !== null) || achados[0] || null;
}

export function campo(rotulo) {
  return cy.document().then((doc) => {
    const el = acharControle(doc, norma(rotulo));
    expect(el, `campo \`${rotulo}\``).to.exist;
    return cy.wrap(el, { log: false });
  });
}

// `cy.contains(":visible", x)` casaria com o `<body>`, que é visível e cujo textContent
// inclui o formulário escondido da outra aba - "não está na tela" nunca falharia. Aqui
// só conta o elemento visível que contém o texto e não tem filho que também o contenha.
function comTexto($corpo, alvo) {
  const re = regex(alvo);
  return $corpo
    .find(":visible")
    .filter(
      (_, el) =>
        re.test(el.textContent || el.value || "") &&
        ![...el.children].some((filho) => re.test(filho.textContent || "")),
    );
}

export function temTexto(alvo) {
  return cy
    .get("body")
    .should(($c) => expect(comTexto($c, alvo), `na tela: ${alvo}`).to.have.length.above(0));
}

export function naoTemTexto(alvo) {
  return cy
    .get("body")
    .should(($c) => expect(comTexto($c, alvo), `fora da tela: ${alvo}`).to.have.length(0));
}

export function aba(nome) {
  return cy.contains(
    "button:visible, a:visible, li:visible, span:visible, [role=tab]:visible",
    new RegExp(`^\\s*${nome}\\s*$`),
  );
}

export function enviar() {
  return cy
    .contains(
      "button:visible, input[type=submit]:visible, a:visible",
      /Enviar solicita/i,
    )
    .click();
}

// Valor plausível por rótulo, não por `name` ou `id`: há run cujos inputs não têm nem um
// nem outro, e aí um default heurístico preenche CEP e data com lixo e o submit nativo
// barra o envio - o critério reprovaria por falha do avaliador.
const PADRAO = {
  "NOME COMPLETO - SEM ABREVIAR": "João da Silva",
  "N. USP": "7654321",
  PROGRAMA: "Matemática Aplicada",
  NÍVEL: "Mestrado",
  "TIPO DE AUXÍLIO": "Participação em evento",
  "E-MAIL": "joao.souza@usp.br",
  "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Brasileiro de Matemática",
  "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/03/2026 a 14/03/2026",
  "CIDADE DO EVENTO, EXAME OU DEFESA": "Campinas",
  "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
  "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
  "LINK DO EVENTO, EXAME OU DEFESA": "https://exemplo.usp.br/evento",
  "VALOR SOLICITADO (R$)": "150000",
  "DETALHAMENTO DO PEDIDO": "Passagem aérea e hospedagem durante o evento.",
  "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
  "DATA DE NASCIMENTO": "01021980",
  LOGRADOURO: "Rua do Matão",
  NÚMERO: "1010",
  COMPLEMENTO: "Bloco A",
  BAIRRO: "Butantã",
  CEP: "05508090",
  CIDADE: "São Paulo",
  ESTADO: "SP",
  "CPF (SEPARADOS POR PONTOS E TRAÇO)": "52998224725",
  "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
  "NOME DO BANCO": "Banco do Brasil",
  "NÚMERO DA AGÊNCIA": "1234",
  "NÚMERO DA CONTA": "56789-0",
};

function escrever(el, valor) {
  if (el.tagName === "SELECT") {
    const opcao =
      [...el.options].find((o) => norma(o.textContent) === norma(valor)) ||
      [...el.options].find((o) => o.value !== "" && !o.disabled);
    if (opcao) cy.wrap(el).select(opcao.value, { force: true });
  } else if (el.type === "radio" || el.type === "checkbox") {
    cy.wrap(el).check({ force: true });
  } else {
    cy.wrap(el).clear({ force: true }).type(valor, { force: true, delay: 0 }).blur();
  }
}

export function preencher(valores = {}) {
  for (const [rotulo, valor] of Object.entries({ ...PADRAO, ...valores })) {
    cy.document().then((doc) => {
      const el = acharControle(doc, norma(rotulo));
      // Campo ausente é campo da outra aba: `NÍVEL` e `TIPO DE AUXÍLIO` só existem em
      // `ALUNOS`, e exigi-los aqui reprovaria a aba `DOCENTES` por engano.
      if (el) escrever(el, valor);
    });
  }
  // Campo que a run inventou e o requisito não prevê: vazio e obrigatório, barraria o
  // envio pela validação nativa do browser.
  cy.get(controles).filter(":visible").each(($el) => {
    if (!$el[0].value) escrever($el[0], "Teste");
  });
}
