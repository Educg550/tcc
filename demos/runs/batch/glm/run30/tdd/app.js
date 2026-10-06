"use strict";

const RE_CPF = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/;
const RE_CEP = /^\d{5}-\d{3}$/;
const RE_DATA = /^\d{2}\/\d{2}\/\d{4}$/;

// Formata o valor: os dígitos digitados são os centavos.
function formataValor(texto) {
  const digitos = texto.replace(/\D/g, "");
  if (!digitos) return "";
  const centavos = digitos.slice(0, 12).padStart(3, "0");
  const inteiro = centavos.slice(0, -2);
  const dec = centavos.slice(-2);
  return "R$ " + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + dec;
}

// Formata CPF: 12345678909 -> 123.456.789-09
function formataCpf(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 11);
  let r = d.slice(0, 3);
  if (d.length > 3) r += "." + d.slice(3, 6);
  if (d.length > 6) r += "." + d.slice(6, 9);
  if (d.length > 9) r += "-" + d.slice(9, 11);
  return r;
}

// Formata CEP: 05508090 -> 05508-090
function formataCep(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

// Formata data de nascimento: 01021980 -> 01/02/1980
function formataDataNascimento(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += "/" + d.slice(2, 4);
  if (d.length > 4) r += "/" + d.slice(4, 8);
  return r;
}

// Valida os dígitos verificadores do CPF.
function cpfValido(cpf) {
  const d = cpf.replace(/\D/g, "");
  if (d.length !== 11) return false;
  let soma = 0;
  for (let i = 0; i < 9; i++) soma += parseInt(d[i]) * (10 - i);
  let dv1 = (soma * 10) % 11;
  if (dv1 === 10) dv1 = 0;
  if (dv1 !== parseInt(d[9])) return false;
  soma = 0;
  for (let i = 0; i < 10; i++) soma += parseInt(d[i]) * (11 - i);
  let dv2 = (soma * 10) % 11;
  if (dv2 === 10) dv2 = 0;
  return dv2 === parseInt(d[10]);
}

// Confere se a data de nascimento é uma data existente.
function dataNascimentoValida(valor) {
  const m = valor.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return false;
  const dia = parseInt(m[1], 10);
  const mes = parseInt(m[2], 10);
  const ano = parseInt(m[3], 10);
  if (mes < 1 || mes > 12) return false;
  const diasNoMes = [31, (ano % 4 === 0 && ano % 100 !== 0) || ano % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  return dia >= 1 && dia <= diasNoMes[mes - 1];
}

function mostraErros(form, erros) {
  const div = form.querySelector(".erros");
  div.innerHTML = "";
  erros.forEach(function (msg) {
    const p = document.createElement("p");
    p.className = "erro";
    p.textContent = msg;
    div.appendChild(p);
  });
}

function ativaAba(alvo) {
  document.querySelectorAll(".aba").forEach(function (aba) {
    const ativa = aba.dataset.aba === alvo;
    aba.classList.toggle("ativa", ativa);
    aba.setAttribute("aria-selected", ativa ? "true" : "false");
  });
  document.querySelectorAll(".painel").forEach(function (painel) {
    painel.hidden = painel.dataset.aba !== alvo;
  });
}

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    ativaAba(aba.dataset.aba);
  });
});

document.querySelectorAll("[data-valor]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formataValor(campo.value);
  });
});

document.querySelectorAll("[data-cpf]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formataCpf(campo.value);
  });
});

document.querySelectorAll("[data-cep]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formataCep(campo.value);
  });
});

document.querySelectorAll("[data-nascimento]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formataDataNascimento(campo.value);
  });
});

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    const dados = new FormData(form);
    dados.append("aba", form.dataset.aba);
    fetch("/solicitacao", { method: "POST", body: dados })
      .then(function (resposta) { return resposta.json(); })
      .then(function (json) {
        if (json.ok) {
          document.getElementById("confirmacao").hidden = false;
          document.getElementById("titulo-confirmacao").textContent = "Solicitação registrada";
          document.getElementById("oficio").textContent = json.oficio;
          document.getElementById("pagina").hidden = true;
        } else {
          mostraErros(form, json.erros);
        }
      });
  });
});
