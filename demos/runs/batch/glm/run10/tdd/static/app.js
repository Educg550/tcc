"use strict";

var FORM_ALUNOS = document.getElementById("form-alunos");
var FORM_DOCENTES = document.getElementById("form-docentes");
var LISTA_ERROS = document.getElementById("erro-lista");
var CONFIRMACAO = document.getElementById("confirmacao");
var OFICIO = document.getElementById("oficio");

var FORMATADORES = {
  valor_solicitado: function (valor) {
    var digitos = valor.replace(/\D/g, "");
    if (digitos === "") {
      return "";
    }
    var centavos = parseInt(digitos, 10);
    var inteiro = Math.floor(centavos / 100);
    var resto = ("0" + (centavos % 100)).slice(-2);
    var partes = [];
    while (inteiro > 0 || partes.length === 0) {
      partes.unshift(("00" + (inteiro % 1000)).slice(-3));
      inteiro = Math.floor(inteiro / 1000);
    }
    var texto = partes.join(".").replace(/^0+/, "");
    if (texto === "") {
      texto = "0";
    }
    return "R$ " + texto + "," + resto;
  },
  cpf: function (valor) {
    var digitos = valor.replace(/\D/g, "").slice(0, 11);
    return digitos.replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/(\d{3})\.(\d{3})\.(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
  },
  cep: function (valor) {
    var digitos = valor.replace(/\D/g, "").slice(0, 8);
    if (digitos.length > 5) {
      return digitos.slice(0, 5) + "-" + digitos.slice(5);
    }
    return digitos;
  },
  data_nascimento: function (valor) {
    var digitos = valor.replace(/\D/g, "").slice(0, 8);
    if (digitos.length > 4) {
      return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
    }
    if (digitos.length > 2) {
      return digitos.slice(0, 2) + "/" + digitos.slice(2);
    }
    return digitos;
  }
};

function aoSairDoCampo(campo) {
  var formatador = FORMATADORES[campo.name];
  if (formatador) {
    campo.value = formatador(campo.value);
  }
}

function prepararFormulario(form) {
  Array.prototype.forEach.call(form.elements, function (campo) {
    campo.addEventListener("blur", function () { aoSairDoCampo(campo); });
  });
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    Array.prototype.forEach.call(form.elements, aoSairDoCampo);
    enviar(form);
  });
}

function enviar(form) {
  var aba = form === FORM_ALUNOS ? "alunos" : "docentes";
  var dados = { aba: aba };
  Array.prototype.forEach.call(form.elements, function (campo) {
    if (campo.name) {
      dados[campo.name] = campo.value;
    }
  });
  var corpo = JSON.stringify(dados);
  fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: corpo
  }).then(function (resposta) {
    return resposta.json().then(function (corpoResposta) { return { ok: resposta.ok, corpo: corpoResposta }; });
  }).then(function (resultado) {
    if (resultado.ok) {
      mostrarOficio(resultado.corpo.oficio);
    } else {
      mostrarErros(resultado.corpo.errors);
    }
  });
}

function mostrarErros(erros) {
  LISTA_ERROS.hidden = false;
  while (LISTA_ERROS.firstChild) {
    LISTA_ERROS.removeChild(LISTA_ERROS.firstChild);
  }
  erros.forEach(function (mensagem) {
    var linha = document.createElement("p");
    linha.textContent = mensagem;
    LISTA_ERROS.appendChild(linha);
  });
}

function mostrarOficio(oficio) {
  LISTA_ERROS.hidden = true;
  FORM_ALUNOS.hidden = true;
  FORM_DOCENTES.hidden = true;
  document.querySelector(".abas").hidden = true;
  CONFIRMACAO.hidden = false;
  OFICIO.textContent = oficio;
}

Array.prototype.forEach.call(document.querySelectorAll(".aba"), function (aba) {
  aba.addEventListener("click", function () {
    document.querySelector(".aba.ativa").classList.remove("ativa");
    aba.classList.add("ativa");
    var visivel = aba.dataset.aba === "alunos" ? FORM_ALUNOS : FORM_DOCENTES;
    var oculto = aba.dataset.aba === "alunos" ? FORM_DOCENTES : FORM_ALUNOS;
    visivel.classList.add("visivel");
    oculto.classList.remove("visivel");
    LISTA_ERROS.hidden = true;
  });
});

prepararFormulario(FORM_ALUNOS);
prepararFormulario(FORM_DOCENTES);
