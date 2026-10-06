var abas = document.querySelectorAll(".aba");
var formularios = { alunos: document.getElementById("form-alunos"),
                     docentes: document.getElementById("form-docentes") };
var confirmacao = document.getElementById("confirmacao");
var oficioEl = document.getElementById("oficio");

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelector(".aba.ativa").classList.remove("ativa");
    aba.classList.add("ativa");
    Object.keys(formularios).forEach(function (nome) {
      formularios[nome].classList.toggle("oculto", nome !== aba.dataset.aba);
    });
    confirmacao.classList.add("oculto");
  });
});

function formatarMoeda(input) {
  var digitos = input.value.replace(/\D/g, "");
  if (!digitos) {
    input.value = "";
    return;
  }
  var centavos = parseInt(digitos, 10);
  var reais = Math.floor(centavos / 100);
  var resto = ("" + (centavos % 100)).padStart(2, "0");
  var partes = [];
  while (reais >= 1000) {
    partes.unshift(("" + (reais % 1000)).padStart(3, "0"));
    reais = Math.floor(reais / 1000);
  }
  partes.unshift("" + reais);
  input.value = "R$ " + partes.join(".") + "," + resto;
}

function formatarPadrao(valor, tamanho) {
  var digitos = valor.replace(/\D/g, "").slice(0, tamanho);
  if (valor === "") return "";
  return digitos;
}

function formatarCpf(input) {
  var d = input.value.replace(/\D/g, "").slice(0, 11);
  if (!d) { input.value = ""; return; }
  input.value = d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, function (_, a, b, c, e) {
    return a + "." + b + "." + c + "-" + e;
  });
}

function formatarCep(input) {
  var d = input.value.replace(/\D/g, "").slice(0, 8);
  input.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(input) {
  var d = input.value.replace(/\D/g, "").slice(0, 8);
  var saida = d.slice(0, 2);
  if (d.length > 2) saida += "/" + d.slice(2, 4);
  if (d.length > 4) saida += "/" + d.slice(4, 8);
  input.value = saida;
}

function aoSair(input) {
  if (input.classList.contains("moeda")) formatarMoeda(input);
  if (input.classList.contains("cpf")) formatarCpf(input);
  if (input.classList.contains("cep")) formatarCep(input);
  if (input.classList.contains("data")) formatarData(input);
}

document.querySelectorAll("input").forEach(function (input) {
  input.addEventListener("blur", function () { aoSair(input); });
});

function enviar(form) {
  var aba = form.dataset.aba;
  var dados = { aba: aba };
  new FormData(form).forEach(function (valor, chave) { dados[chave] = valor; });
  fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  })
    .then(function (r) { return r.json(); })
    .then(function (corpo) {
      var caixa = document.getElementById("erros-" + aba);
      caixa.innerHTML = "";
      corpo.erros.forEach(function (erro) {
        var linha = document.createElement("p");
        linha.textContent = erro;
        caixa.appendChild(linha);
      });
      if (corpo.erros.length === 0) {
        oficioEl.textContent = corpo.oficio;
        document.querySelector("main").classList.add("oculto");
        document.querySelector(".abas").classList.add("oculto");
        confirmacao.classList.remove("oculto");
        confirmacao.scrollIntoView();
      }
    });
  return false;
}

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    enviar(form);
  });
});
