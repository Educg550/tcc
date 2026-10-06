"use strict";

const ABAS = ["alunos", "docentes"];

function alternarAba(aba) {
  document.querySelectorAll(".aba").forEach((botao) => {
    botao.classList.toggle("ativa", botao.dataset.aba === aba);
  });
  document.querySelectorAll(".painel").forEach((painel) => {
    painel.classList.toggle("ativo", painel.id === `form-${aba}`);
  });
}

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => alternarAba(botao.dataset.aba));
});

function apenasDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

function formatarValor(valor) {
  const digitos = apenasDigitos(valor);
  if (!digitos) return "";
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const resto = centavos % 100;
  const reaisTexto = reais.toLocaleString("pt-BR");
  return `R$ ${reaisTexto},${String(resto).padStart(2, "0")}`;
}

function formatarCpf(cpf) {
  const d = apenasDigitos(cpf).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

function formatarCep(cep) {
  const d = apenasDigitos(cep).slice(0, 8);
  if (d.length <= 5) return d;
  return `${d.slice(0, 5)}-${d.slice(5)}`;
}

function formatarData(data) {
  const d = apenasDigitos(data).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}\n