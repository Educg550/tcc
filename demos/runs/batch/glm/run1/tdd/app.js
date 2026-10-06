"use strict";

const ABAS = [...document.querySelectorAll(".aba")];
const PAINEIS = [...document.querySelectorAll(".painel")];
const CONFIRMACAO = document.getElementById("confirmacao");
const OFICIO = document.getElementById("oficio");

function ativaAba(nome) {
  for (const aba of ABAS) aba.classList.toggle("ativa", aba.dataset.aba === nome);
  for (const painel of PAINEIS) painel.hidden = painel.dataset.aba !== nome;
  CONFIRMACAO.hidden = true;
}

ABAS.forEach((aba) => aba.addEventListener("click", () => ativaAba(aba.dataset.aba)));

function soDigitos(texto) {
  return (texto.match(/\d+/g) || []).join("");
}

function formataMoeda(texto) {
  const centavos = soDigitos(texto).replace(/^0+(?=\d)/, "");
  if (!centavos) return "";
  const inteiro = String(Math.floor(Number(centavos) / 100));
  const resto = centavos.slice(-2).padStart(2, "0");
  const milhar = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${milhar},${resto}`;
}

function formataCpf(digitos) {
  return digitos.slice(0, 11).replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
}

function formataCep(digitos) {
  return digitos.slice(0, 8).replace(/(\d{5})(\d{3})/, "$1-$2");
}

function formataData(digitos) {
  return digitos.slice(0, 8).replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
}

const FORMATADORES = [
  [".moeda", formataMoeda],
  [".cpf", formataCpf],
  [".cep", formataCep],
  [".data", formataData],
];

for (const [seletor, formatar] of FORMATADORES) {
  for (const campo of document.querySelectorAll(seletor)) {
    campo.addEventListener("blur", () => {
      campo.value = formatar(campo.value);
    });
  }
}

function abaAtiva() {
  return PAINEIS.find((painel) => !painel.hidden);
}

function mostraErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.innerHTML = "";
  for (const mensagem of erros) {
    const linha = document.createElement("p");
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  }
  caixa.hidden = erros.length === 0;
}

async function envia(form) {
  const dados = Object.fromEntries(new FormData(form).entries());
  dados.perfil = form.dataset.aba;
  const resposta = await fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const resultado = await resposta.json();
  if (resultado.erros) {
    mostraErros(form, resultado.erros);
    return;
  }
  mostraErros(form, []);
  OFICIO.textContent = resultado.oficio;
  CONFIRMACAO.hidden = false;
  for (const painel of PAINEIS) painel.hidden = true;
  for (const aba of ABAS) aba.classList.remove("ativa");
  document.querySelector(".abas").hidden = true;
  window.scrollTo(0, 0);
}

for (const form of PAINEIS) {
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    envia(form);
  });
}
