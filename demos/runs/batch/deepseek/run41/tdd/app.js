"use strict";

(function () {
  var abas = document.querySelectorAll(".aba");
  var paineis = {
    ALUNOS: document.getElementById("painel-ALUNOS"),
    DOCENTES: document.getElementById("painel-DOCENTES")
  };
  var confirmacao = document.getElementById("confirmacao");

  Array.prototype.forEach.call(abas, function (aba) {
    aba.addEventListener("click", function () {
      Array.prototype.forEach.call(abas, function (outra) {
        outra.classList.remove("ativa");
      });
      aba.classList.add("ativa");
      Object.keys(paineis).forEach(function (nome) {
        paineis[nome].classList.toggle("oculto", nome !== aba.dataset.aba);
      });
    });
  });

  function digitos(texto) {
    return (texto || "").replace(/[^0-9]/g, "");
  }

  var formatadores = {
    valor_solicitado: function (texto) {
      var d = digitos(texto);
      if (!d) {
        return "";
      }
      var total = parseInt(d, 10);
      var reais = Math.floor(total / 100).toLocaleString("pt-BR");
      var centavos = ("0" + (total % 100)).slice(-2);
      return "R$ " + reais + "," + centavos;
    },
    cpf: function (texto) {
      var d = digitos(texto).slice(0, 11);
      return d
        .replace(/^([0-9]{3})([0-9])/, "$1.$2")
        .replace(/^([0-9]{3})[.]([0-9]{3})([0-9])/, "$1.$2.$3")
        .replace(/^([0-9]{3})[.]([0-9]{3})[.]([0-9]{3})([0-9])/, "$1.$2.$3-$4");
    },
    cep: function (texto) {
      var d = digitos(texto).slice(0, 8);
      return d.replace(/^([0-9]{5})([0-9])/, "$1-$2");
    },
    data_nascimento: function (texto) {
      var d = digitos(texto).slice(0, 8);
      return d
        .replace(/^([0-9]{2})([0-9])/, "$1/$2")
        .replace(/^([0-9]{2})[/]([0-9]{2})([0-9])/, "$1/$2/$3");
    }
  };

  Array.prototype.forEach.call(document.querySelectorAll(".formulario"), function (formulario) {
    Object.keys(formatadores).forEach(function (nome) {
      var campo = formulario.querySelector('[name="' + nome + '"]');
      campo.addEventListener("blur", function () {
        campo.value = formatadores[nome](campo.value);
      });
    });

    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(formulario).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      dados.aba = formulario.dataset.aba;
      var area = formulario.querySelector(".erros");
      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (retorno) {
          area.innerHTML = "";
          if (retorno.ok) {
            mostrarConfirmacao(retorno.oficio);
            return;
          }
          (retorno.erros || []).forEach(function (mensagem) {
            var paragrafo = document.createElement("p");
            paragrafo.textContent = mensagem;
            area.appendChild(paragrafo);
          });
        });
    });
  });

  function mostrarConfirmacao(oficio) {
    document.querySelector(".abas").classList.add("oculto");
    paineis.ALUNOS.classList.add("oculto");
    paineis.DOCENTES.classList.add("oculto");
    confirmacao.querySelector(".oficio").textContent = oficio;
    confirmacao.classList.remove("oculto");
  }
})();
