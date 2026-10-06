(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      formularios.forEach(function (form) {
        form.classList.toggle("ativo", form.dataset.aba === aba.dataset.aba);
      });
    });
  });

  function digitos(valor) {
    return (valor || "").replace(/\D/g, "");
  }

  function formatarValor(valor) {
    var d = digitos(valor);
    if (!d) {
      return "";
    }
    var numero = parseInt(d, 10) / 100;
    return "R$ " + numero.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function formatarCPF(valor) {
    return digitos(valor).slice(0, 11)
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
  }

  function formatarCEP(valor) {
    return digitos(valor).slice(0, 8)
      .replace(/^(\d{5})(\d)/, "$1-$2");
  }

  function formatarData(valor) {
    return digitos(valor).slice(0, 8)
      .replace(/^(\d{2})(\d)/, "$1/$2")
      .replace(/^(\d{2})\/(\d{2})(\d)/, "$1/$2/$3");
  }

  var formatadores = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  formularios.forEach(function (form) {
    Array.prototype.forEach.call(form.querySelectorAll("input[name]"), function (campo) {
      var formatar = formatadores[campo.name];
      if (formatar) {
        campo.addEventListener("blur", function () {
          campo.value = formatar(campo.value);
        });
      }
    });

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      Array.prototype.forEach.call(new FormData(form).entries(), function (par) {
        dados[par[0]] = par[1];
      });
      dados.aba = form.dataset.aba;

      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          var caixa = form.querySelector(".erros");
          if (resultado.erros) {
            caixa.textContent = "";
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement("div");
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            caixa.hidden = false;
            return;
          }
          caixa.hidden = true;
          document.getElementById("painel").hidden = true;
          document.querySelector(".abas").hidden = true;
          document.getElementById("oficio").textContent = resultado.oficio;
          document.getElementById("confirmacao").hidden = false;
        });
    });
  });
})();
