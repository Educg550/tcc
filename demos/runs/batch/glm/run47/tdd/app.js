"use strict";

/* Alternância entre as abas ALUNOS e DOCENTES: a aba clicada passa a ser a
   ativa e a outra apenas se esconde - a página não recarrega e o que já foi
   digitado na aba que sai de vista continua lá. */
const botoes = document.querySelectorAll(".abas button");

function ativarAba(aba) {
  for (const botao of botoes) {
    botao.classList.toggle("ativa", botao.dataset.aba === aba);
  }
  document.getElementById("aba-alunos").hidden = aba !== "alunos";
  document.getElementById("aba-docentes").hidden = aba !== "docentes";
}

for (const botao of botoes) {
  botao.addEventListener("click", () => ativarAba(botao.dataset.aba));
}

/* Quatro campos reformatam o que foi digitado no momento em que o campo
   perde o foco: o usuário digita apenas dígitos, a pontuação é da aplicação. */
function soDigitos(texto) {
  return (texto.match(/\d/g) || []).join("");
}

/* Moeda brasileira: os dígitos digitados são os centavos do valor.
   "1500" vira "R$ 15,00"; "150000" vira "R$ 1.500,00". */
function formatarMoeda(digitos) {
  if (!digitos) return "";
  const centavos = digitos.padStart(3, "0");
  const reais = centavos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + centavos.slice(-2);
}

/* CPF: "12345678909" vira "123.456.789-09". */
function formatarCpf(digitos) {
  const cpf = digitos.slice(0, 11);
  const grupos = [cpf.slice(0, 3), cpf.slice(3, 6), cpf.slice(6, 9)].filter(Boolean);
  let texto = grupos.join(".");
  if (cpf.length > 9) texto += "-" + cpf.slice(9);
  return texto;
}

/* CEP: "05508090" vira "05508-090". */
function formatarCep(digitos) {
  const cep = digitos.slice(0, 8);
  return cep.length > 5 ? cep.slice(0, 5) + "-" + cep.slice(5) : cep;
}

/* Data de nascimento: "01021980" vira "01/02/1980". */
function formatarData(digitos) {
  const data = digitos.slice(0, 8);
  if (data.length > 4) return data.slice(0, 2) + "/" + data.slice(2, 4) + "/" + data.slice(4);
  if (data.length > 2) return data.slice(0, 2) + "/" + data.slice(2);
  return data;
}

const formatadores = [
  [".moeda", formatarMoeda],
  [".cpf", formatarCpf],
  [".cep", formatarCep],
  [".data", formatarData],
];

for (const [seletor, formatar] of formatadores) {
  for (const campo of document.querySelectorAll(seletor)) {
    campo.addEventListener("blur", () => {
      campo.value = formatar(soDigitos(campo.value));
    });
  }
}

/* Envio: quem decide se a solicitação é válida é o backend. Com erro, as
   mensagens dele aparecem no topo do formulário da aba ativa, uma por
   linha; com sucesso, a tela passa a mostrar a confirmação com o ofício. */
function mostrarErros(painel, mensagens) {
  painel.textContent = "";
  for (const mensagem of mensagens) {
    const linha = document.createElement("p");
    linha.textContent = mensagem;
    painel.appendChild(linha);
  }
  painel.hidden = mensagens.length === 0;
}

function mostrarOficio(oficio) {
  document.querySelector(".pagina-titulo").hidden = true;
  document.querySelector(".abas").hidden = true;
  document.querySelector("main").hidden = true;
  document.getElementById("oficio").textContent = oficio;
  document.getElementById("confirmacao").hidden = false;
}

async function enviarSolicitacao(form) {
  const dados = { aba: form.dataset.aba.toUpperCase() };
  for (const [nome, valor] of new FormData(form).entries()) {
    dados[nome] = valor;
  }
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const corpo = await resposta.json();
  if (!resposta.ok) {
    mostrarErros(document.getElementById("erros-" + form.dataset.aba), corpo.erros);
    return;
  }
  mostrarOficio(corpo.oficio);
}

for (const form of document.querySelectorAll("form")) {
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviarSolicitacao(form);
  });
}
