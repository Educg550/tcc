"use strict";

function formatarMoeda(texto) {
var digitos = texto.replace(/\D/g, "");
if (!digitos) { return ""; }
var centavos = digitos.slice(-2).padStart(2, "0");
var reais = digitos.slice(0, -2);
if (reais === "") { reais = "0"; }
var grupos = [];
while (reais.length > 3) {
grupos.unshift(reais.slice(-3));
reais = reais.slice(0, -3);
}
grupos.unshift(reais);
return "R$ " + grupos.join(".") + "," + centavos;
}

function formatarCPF(texto) {
var d = texto.replace(/\D/g, "").slice(0, 11);
if (d.length !== 11) { return d; }
return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCEP(texto) {
var d = texto.replace(/\D/g, "").slice(0, 8);
if (d.length !== 8) { return d; }
return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(texto) {
var d = texto.replace(/\D/g, "").slice(0, 8);
if (d.length !== 8) { return d; }
return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

function aoSairDoCampo(campo, formatador) {
campo.addEventListener("blur", function () {
campo.value = formatador(campo.value);
});
}

document.querySelectorAll("input.moeda").forEach(function (campo) {
aoSairDoCampo(campo, formatarMoeda);
});
document.querySelectorAll("input.cpf").forEach(function (campo) {
aoSairDoCampo(campo, formatarCPF);
});
document.querySelectorAll("input.cep").forEach(function (campo) {
aoSairDoCampo(campo, formatarCEP);
});
document.querySelectorAll("input.data").forEach(function (campo) {
aoSairDoCampo(campo, formatarData);
});

var abas = [
{ botao: document.getElementById("aba-alunos"), painel: document.getElementById("painel-alunos"), erros: document.getElementById("erros-alunos") },
{ botao: document.getElementById("aba-docentes"), painel: document.getElementById("painel-docentes"), erros: document.getElementById("erros-docentes") }
];

abas.forEach(function (aba) {
aba.botao.addEventListener("click", function () {
abas.forEach(function (outra) {
outra.botao.classList.remove("ativa");
outra.botao.setAttribute("aria-selected", "false");
outra.painel.classList.remove("ativo");
});
aba.botao.classList.add("ativa");
aba.botao.setAttribute("aria-selected", "true");
aba.painel.classList.add("ativo");
});
});

function mostrarErros(elemento, erros) {
elemento.textContent = erros.join("\n");
elemento.classList.add("ativa");
}

function esconderErros(elemento) {
elemento.textContent = "";
elemento.classList.remove("ativa");
}

document.querySelectorAll("form.formulario").forEach(function (form) {
form.addEventListener("submit", function (evento) {
evento.preventDefault();
var dados = new FormData(form);
dados.append("perfil", form.getAttribute("data-perfil"));
fetch("/enviar", { method: "POST", body: dados })
.then(function (resposta) {
return resposta.json().then(function (corpo) {
return { status: resposta.status, corpo: corpo };
});
})
.then(function (resultado) {
if (resultado.status === 400) {
mostrarErros(document.querySelector("#erros-" + form.getAttribute("data-perfil")), resultado.corpo.erros);
return;
}
esconderErros(document.querySelector("#erros-" + form.getAttribute("data-perfil")));
var confirmacao = document.getElementById("confirmacao");
document.getElementById("oficio").textContent = resultado.corpo.oficio;
document.querySelector(".conteudo").style.display = "none";
document.querySelector(".cabecalho").insertAdjacentElement("afterend", confirmacao);
confirmacao.hidden = false;
confirmacao.classList.add("ativa");
confirmacao.scrollIntoView();
});
});
});

document.getElementById("nova").addEventListener("click", function () {
var confirmacao = document.getElementById("confirmacao");
confirmacao.hidden = true;
confirmacao.classList.remove("ativa");
document.querySelector(".conteudo").style.display = "";
document.getElementById("oficio").textContent = "";
});
