// Abas: trocar sem recarregar, sem perder o que foi digitado.
document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("active"); });
    botao.classList.add("active");
    var aba = botao.dataset.aba;
    document.getElementById("alunos").hidden = aba !== "alunos";
    document.getElementById("docentes").hidden = aba !== "docentes";
  });
});

// Formatação de moeda: dígitos digitados são os centavos do valor.
function formatarValor(digitos) {
  var limpos = digitos.replace(/[^0-9]/g, "").replace(/^0+/, "") || "0";
  var texto = (limpos + "00").slice(0, Math.max(3, limpos.length));
  var inteiro = texto.slice(0, -2);
  var centavos = texto.slice(-2);
  var partes = [];
  while (inteiro.length > 3) {
    partes.unshift(inteiro.slice(-3));
    inteiro = inteiro.slice(0, -3);
  }
  partes.unshift(inteiro);
  return "R$ " + partes.join(".") + "," + centavos;
}

function formatarCPF(digitos) {
  var d = digitos.replace(/[^0-9]/g, "").slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function formatarCEP(digitos) {
  var d = digitos.replace(/[^0-9]/g, "").slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(digitos) {
  var d = digitos.replace(/[^0-9]/g, "").slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

// Os quatro campos reformatam no momento em que o usuário sai deles (blur).
document.querySelectorAll("input").forEach(function (campo) {
  if (campo.classList.contains("campo-moeda")) {
    campo.addEventListener("blur", function () {
      if (campo.value.trim() !== "") campo.value = formatarValor(campo.value);
    });
  }
  if (campo.classList.contains("campo-cpf")) {
    campo.addEventListener("blur", function () {
      campo.value = formatarCPF(campo.value);
    });
  }
  if (campo.classList.contains("campo-cep")) {
    campo.addEventListener("blur", function () {
      campo.value = formatarCEP(campo.value);
    });
  }
  if (campo.classList.contains("campo-data")) {
    campo.addEventListener("blur", function () {
      campo.value = formatarData(campo.value);
    });
  }
});

function mostrarErros(aba, erros) {
  var bloco = document.getElementById("erros-" + aba);
  bloco.textContent = "";
  erros.forEach(function (msg) {
    var p = document.createElement("p");
    p.textContent = msg;
    bloco.appendChild(p);
  });
  bloco.hidden = erros.length === 0;
}

function enviarFormulario(form, aba) {
  fetch("/solicitar/" + aba, { method: "POST", body: new FormData(form) })
    .then(function (r) { return r.json(); })
    .then(function (resposta) {
      mostrarErros(aba, resposta.erros);
      if (resposta.ok) {
        document.querySelector("main").hidden = true;
        document.querySelector(".abas").hidden = true;
        document.getElementById("oficio").textContent = resposta.oficio;
        document.getElementById("confirmacao").hidden = false;
      }
    });
}

document.getElementById("form-alunos").addEventListener("submit", function (e) {
  e.preventDefault();
  enviarFormulario(e.target, "alunos");
});

document.getElementById("form-docentes").addEventListener("submit", function (e) {
  e.preventDefault();
  enviarFormulario(e.target, "docentes");
});
