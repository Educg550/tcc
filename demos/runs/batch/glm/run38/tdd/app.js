"use strict";

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  var digitos = soDigitos(texto);
  if (!digitos) {
    return "";
  }
  var centavos = parseInt(digitos, 10);
  var reais = Math.floor(centavos / 100);
  var resto = String(centavos % 100);
  while (resto.length < 2) {
    resto = "0" + resto;
  }
  var milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + milhar + "," + resto;
}

function formatarCpf(texto) {
  var digitos = soDigitos(texto);
  if (digitos.length === 11) {
    return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." + digitos.slice(6, 9) + "-" + digitos.slice(9);
  }
  return digitos;
}

function formatarCep(texto) {
  var digitos = soDigitos(texto);
  if (digitos.length === 8) {
    return digitos.slice(0, 5) + "-" + digitos.slice(5);
  }
  return digitos;
}

function formatarData(texto) {
  var digitos = soDigitos(texto);
  if (digitos.length === 8) {
    return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
  }
  return digitos;
}

var mascaras = [
  ["js-moeda", formatarMoeda],
  ["js-cpf", formatarCpf],
  ["js-cep", formatarCep],
  ["js-data", formatarData],
];

mascaras.forEach(function (mascara) {
  document.querySelectorAll("." + mascara[0]).forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = mascara[1](campo.value);
    });
  });
});

var abas = document.querySelectorAll(".aba");
var formularios = document.querySelectorAll("form");

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    formularios.forEach(function (form) {
      form.hidden = form.dataset.tipo !== aba.dataset.aba;
    });
  });
});

formularios.forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var erros = form.querySelector(".erros");
    erros.hidden = true;
    erros.textContent = "";
    var dados = { tipo: form.dataset.tipo };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then(function (resposta) {
        return resposta.json().then(function (corpo) {
          return { ok: resposta.ok, corpo: corpo };
        });
      })
      .then(function (resultado) {
        if (resultado.ok) {
          document.getElementById("oficio").textContent = resultado.corpo.oficio;
          document.getElementById("solicitacao").hidden = true;
          document.getElementById("confirmacao").hidden = false;
          return;
        }
        resultado.corpo.erros.forEach(function (mensagem) {
          var item = document.createElement("li");
          item.textContent = mensagem;
          erros.appendChild(item);
        });
        erros.hidden = false;
      });
  });
});

document.getElementById("nova-solicitacao").addEventListener("click", function () {
  formularios.forEach(function (form) {
    form.reset();
    var erros = form.querySelector(".erros");
    erros.hidden = true;
    erros.textContent = "";
  });
  document.getElementById("confirmacao").hidden = true;
  document.getElementById("solicitacao").hidden = false;
});
