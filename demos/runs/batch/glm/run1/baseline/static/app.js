document.querySelectorAll(".aba").forEach(function (b) {
b.addEventListener("click", function () {
document.querySelectorAll(".aba").forEach(function (x) { x.classList.remove("ativa"); });
b.classList.add("ativa");
document.querySelectorAll(".painel").forEach(function (p) { p.classList.remove("visivel"); });
document.getElementById("form-" + b.dataset.aba).classList.add("visivel");
});
});

function formatarCampo(nome, fn) {
document.querySelectorAll('input[name="' + nome + '"]').forEach(function (inp) {
inp.addEventListener("blur", function () {
var digitos = inp.value.replace(/\D/g, "");
var v = fn(digitos);
if (v !== null) { inp.value = v; }
});
});
}

formatarCampo("valor", function (d) {
if (!d) { return ""; }
var centavos = parseInt(d, 10);
var reais = Math.floor(centavos / 100);
var cent = centavos % 100;
var s = String(reais);
var grupos = [];
while (s.length > 3) { grupos.unshift(s.slice(-3)); s = s.slice(0, -3); }
grupos.unshift(s);
return "R$ " + grupos.join(".") + "," + String(cent).padStart(2, "0");
});

formatarCampo("cpf", function (d) {
if (!d) { return ""; }
return d.slice(0, 11).replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, function (_, a, b, c, e) {
return a + "." + b + "." + c + "-" + e;
});
});

formatarCampo("cep", function (d) {
if (!d) { return ""; }
return d.slice(0, 8).replace(/(\d{5})(\d{0,3})/, "$1-$2");
});

formatarCampo("nascimento", function (d) {
if (!d) { return ""; }
return d.slice(0, 8).replace(/(\d{2})(\d{2})(\d{0,4})/, "$1/$2/$3");
});

function abaAtiva() {
return document.querySelector(".aba.ativa").dataset.aba;
}

document.querySelectorAll("form.painel").forEach(function (form) {
form.addEventListener("submit", function (ev) {
ev.preventDefault();
var aba = form.id.replace("form-", "");
var dados = {};
new FormData(form).forEach(function (v, k) { dados[k] = v; });
fetch("/api/solicitacao", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({ aba: aba, dados: dados })
}).then(function (r) { return r.json(); }).then(function (res) {
if (res.ok) {
document.getElementById("oficio").textContent = res.oficio;
document.querySelectorAll(".painel").forEach(function (p) { p.style.display = "none"; });
document.querySelector(".abas").style.display = "none";
document.querySelector(".erros").classList.remove("visivel");
document.getElementById("confirmacao").classList.remove("oculto");
} else {
var box = document.getElementById("erros");
box.innerHTML = "";
res.erros.forEach(function (e) {
var p = document.createElement("p");
p.textContent = e;
box.appendChild(p);
});
box.classList.add("visivel");
}
});
});
});
