document.addEventListener("DOMContentLoaded", function () {
 var abaAtual = "alunos";
 var erros = document.getElementById("erros");
 var confirmacao = document.getElementById("confirmacao");
 var oficio = document.getElementById("oficio");

 document.querySelectorAll(".aba").forEach(function (botao) {
 botao.addEventListener("click", function () {
 abaAtual = botao.dataset.aba;
 document.querySelectorAll(".aba").forEach(function (b) {
 b.classList.toggle("ativa", b === botao);
 });
 document.getElementById("form-alunos").hidden = abaAtual !== "alunos";
 document.getElementById("form-docentes").hidden = abaAtual !== "docentes";
 });
 });

 function formatarCampo(nome, funcao) {
 var campo = document.querySelector('[name="' + nome + '"]');
 if (!campo) return;
 campo.addEventListener("blur", function () {
 var valor = funcao(campo.value);
 if (valor !== null && valor !== undefined) {
 campo.value = valor;
 }
 });
 }

 function formatarMoeda(texto) {
 var digitos = (texto || "").replace(/\D/g, "");
 if (!digitos) return "";
 var centavos = parseInt(digitos, 10);
 var reais = Math.floor(centavos / 100);
 var resto = (centavos % 100).toString().padStart(2, "0");
 return "R$ " + reais.toLocaleString("pt-BR") + "," + resto;
 }

 function formatarCpf(texto) {
 var d = (texto || "").replace(/\D/g, "").slice(0, 11);
 return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
 }

 function formatarCep(texto) {
 var d = (texto || "").replace(/\D/g, "").slice(0, 8);
 return d.length === 8 ? d.slice(0, 5) + "-" + d.slice(5) : d;
 }

 function formatarData(texto) {
 var d = (texto || "").replace(/\D/g, "").slice(0, 8);
 return d.length === 8 ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4) : d;
 }

 formatarCampo("valor", formatarMoeda);
 formatarCampo("cpf", formatarCpf);
 formatarCampo("cep", formatarCep);
 formatarCampo("nascimento", formatarData);

 document.querySelectorAll("form").forEach(function (form) {
 form.addEventListener("submit", function (evento) {
 evento.preventDefault();
 var dados = { aba: abaAtual };
 new FormData(form).forEach(function (valor, chave) {
 dados[chave] = valor;
 });
 var comuns = document.getElementById("form-endereco");
 var pagamento = document.getElementById("form-pagamento");
 [comuns, pagamento].forEach(function (sec) {
 new FormData(sec.querySelector("form") || sec).forEach(function (v, k) {
 dados[k] = v;
 });
 });
 fetch("/solicitar", {
 method: "POST",
 headers: { "Content-Type": "application/json" },
 body: JSON.stringify(dados),
 })
 .then(function (r) {
 return r.json();
 })
 .then(function (corpo) {
 if (corpo.valido) {
 erros.hidden = true;
 oficio.textContent = corpo.oficio;
 confirmacao.hidden = false;
 document.querySelectorAll(".painel").forEach(function (p) {
 p.hidden = true;
 });
 document.querySelector(".abas").hidden = true;
 } else {
 erros.innerHTML = "";
 corpo.erros.forEach(function (msg) {
 var li = document.createElement("li");
 li.textContent = msg;
 erros.appendChild(li);
 });
 erros.hidden = false;
 }
 });
 });
 });

 document.getElementById("nova").addEventListener("click", function () {
 confirmacao.hidden = true;
 document.querySelector(".abas").hidden = false;
 document.querySelectorAll(".painel").forEach(function (p) {
 p.hidden = false;
 });
 });
});
