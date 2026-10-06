(function () {
"use strict";

var abas = document.querySelectorAll(".aba");
abas.forEach(function (aba) {
aba.addEventListener("click", function () {
var alvo = aba.getAttribute("data-aba");
document.querySelectorAll(".aba").forEach(function (outra) {
var ativa = outra === aba;
outra.classList.toggle("active", ativa);
outra.setAttribute("aria-selected", ativa ? "true" : "false");
});
document.querySelectorAll(".painel").forEach(function (painel) {
painel.hidden = painel.getAttribute("data-painel") !== alvo;
});
});
});

function apenasDigitos(valor) {
return (valor || "").replace(/\D/g, "");
}

function formatarValor(valor) {
var digitos = apenasDigitos(valor);
if (!digitos) { return ""; }
var total = parseInt(digitos, 10);
var centavos = String(total % 100);
if (centavos.length < 2) { centavos = "0" + centavos; }
var reais = String(Math.floor(total / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
return "R$ " + reais + "," + centavos;
}

function formatarCPF(valor) {
var d = apenasDigitos(valor).slice(0, 11);
if (d.length > 9) { return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9); }
if (d.length > 6) { return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6); }
if (d.length > 3) { return d.slice(0, 3) + "." + d.slice(3); }
return d;
}

function formatarCEP(valor) {
var d = apenasDigitos(valor).slice(0, 8);
if (d.length > 5) { return d.slice(0, 5) + "-" + d.slice(5); }
return d;
}

function formatarData(valor) {
var d = apenasDigitos(valor).slice(0, 8);
if (d.length > 4) { return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4); }
if (d.length > 2) { return d.slice(0, 2) + "/" + d.slice(2); }
return d;
}

var mascaras = {
valor: formatarValor,
cpf: formatarCPF,
cep: formatarCEP,
data_nascimento: formatarData
};

document.querySelectorAll("input[name]").forEach(function (campo) {
var mascara = mascaras[campo.name];
if (!mascara) { return; }
campo.addEventListener("blur", function () {
campo.value = mascara(campo.value);
});
});

function mostrarErros(form, mensagens) {
var caixa = form.querySelector(".erros");
caixa.innerHTML = "";
mensagens.forEach(function (mensagem) {
var linha = document.createElement("p");
linha.textContent = mensagem;
caixa.appendChild(linha);
});
caixa.hidden = mensagens.length === 0;
}

function mostrarOficio(texto) {
document.getElementById("formularios").hidden = true;
document.querySelector(".abas").hidden = true;
document.getElementById("oficio").textContent = texto;
document.getElementById("confirmacao").hidden = false;
}

document.querySelectorAll("form").forEach(function (form) {
form.addEventListener("submit", function (evento) {
evento.preventDefault();
var dados = {};
new FormData(form).forEach(function (valor, chave) {
dados[chave] = valor;
});
fetch("/solicitar", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify(dados)
})
.then(function (resposta) { return resposta.json(); })
.then(function (retorno) {
if (retorno.ok) { mostrarOficio(retorno.oficio); }
else { mostrarErros(form, retorno.erros); }
});
});
});
})();
