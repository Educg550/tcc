(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var paineis = document.querySelectorAll(".painel");

  function mostrarAba(nome) {
    abas.forEach(function (botao) {
      var ativa = botao.dataset.aba === nome;
      botao.classList.toggle("ativa", ativa);
      botao.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    paineis.forEach(function (painel) {
      painel.hidden = painel.dataset.aba !== nome;
    });
  }

  abas.forEach(function (botao) {
    botao.addEventListener("click", function () {
      mostrarAba(botao.dataset.aba);
    });
  });

  function soDigitos(valor) {
    return valor.replace(/\D/g, "");
  }

  var formatadores = {
    // os dígitos digitados são os centavos do valor
    moeda: function (valor) {
      var digitos = soDigitos(valor);
      if (!digitos) return "";
      var inteiros = digitos.slice(0, -2).replace(/^0+/, "") || "0";
      var centavos = digitos.slice(-2).padStart(2, "0");
      return "R$ " + inteiros.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
    },
    cpf: function (valor) {
      var digitos = soDigitos(valor);
      if (digitos.length !== 11) return valor;
      return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
    },
    cep: function (valor) {
      var digitos = soDigitos(valor);
      if (digitos.length !== 8) return valor;
      return digitos.replace(/(\d{5})(\d{3})/, "$1-$2");
    },
    data: function (valor) {
      var digitos = soDigitos(valor);
      if (digitos.length !== 8) return valor;
      return digitos.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
    }
  };

  document.querySelectorAll("[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = formatadores[campo.dataset.formato](campo.value);
    });
  });

  paineis.forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();

      var dados = Object.fromEntries(new FormData(formulario).entries());
      dados.aba = formulario.dataset.aba;
      var caixa = formulario.querySelector(".erros");

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resposta) {
          if (resposta.erros && resposta.erros.length) {
            caixa.textContent = resposta.erros.join("\n");
            caixa.hidden = false;
            return;
          }
          caixa.hidden = true;
          document.getElementById("oficio").textContent = resposta.oficio;
          document.getElementById("formularios").hidden = true;
          document.getElementById("confirmacao").hidden = false;
        })
        .catch(function () {
          caixa.textContent = "Não foi possível enviar a solicitação. Tente novamente.";
          caixa.hidden = false;
        });
    });
  });
})();
