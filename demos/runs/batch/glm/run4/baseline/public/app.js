"use strict";

const form = document.querySelector("#solicitacao");
const nome = form.querySelector("#nome");

const LABELS = {
  nome: "Nome completo",
  n_usp: "Nº USP",
  email: "E-mail",
  cep: "CEP",
  valor: "Valor",
};

const EXAMPLES = {
  nome: "Maria da Silva",
  n_usp: "1234567",
  email: "maria@usp.br",
  cep: "05508-090",
  valor: "1500,00",
};

/**
 * Monta o texto do campo de valor a partir dos dígitos digitados.
 *
 * @param {string} digits Os dígitos digitados.
 * @returns {string} O texto formatado.
 */
function buildValor(digits) {
  const padded = digits.padStart(3, "0");
  const inteiros = padded.slice(0, -2);
  const centavos = padded.slice(-2);
  const groups = inteiros.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${groups},${centavos}`;
}

/**
 * Aplica as máscaras monetárias conforme o usuário digita.
 *
 * @param {HTMLInputElement} input O campo de valor.
 */
function aplicarMascaraValor(input) {
  const digits = input.value.replace(/\D/g, "");
  input.value = buildValor(digits);
}

nome.addEventListener("input", () => {
  nome.value = nome.value.toUpperCase();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  console.debug("submetendo", form);
});
