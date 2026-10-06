(function () {
  "use strict";

  var abas = Array.prototype.slice.call(document.querySelectorAll(".aba"));
  var paineis = Array.prototype.slice.call(document.querySelectorAll(".painel"));

  function selecionarAba(nome) {
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
      selecionarAba(botao.dataset.aba);
    });
  });

  var formatadores = {
    moeda: function (valor) {
      var digitos = valor.replace(/\D/g, "").replace(/^0+(?=\d)/, "");
      if (!digitos) { return ""; }
      var centavos = digitos.slice(-2).padStart(2, "0");
      var inteiros = digitos.slice(0, -2).replace(/^0+(?=\d)/, "") || "0";
      inteiros = inteiros.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      return "R$ " + inteiros + "," + centavos;
    },
    cpf: function (valor) {
      var d = valor.replace(/\D/g, "").slice(0, 11);
      var saida = d.slice(0, 3);
      if (d.length > 3) { saida += "." + d.slice(3, 6); }
      if (d.length > 6) { saida += "." + d.slice(6, 9); }
      if (d.length > 9) { saida += "-" + d.slice(9, 11); }
      return saida;
    },
    cep: function (valor) {
      var d = valor.replace(/\D/g, "").slice(0, 8);
      return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
    },
    data: function (valor) {
      var d = valor.replace(/\D/g, "").slice(0, 8);
      if (d.length <= 2) { return d; }
      if (d.length <= 4) { return d.slice(0, 2) + "/" + d.slice(2); }
      return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    }
  };

  Array.prototype.slice.call(document.querySelectorAll("[data-formato]")).forEach(function (campo) {
    campo.addEventListener("blur", function () {
      var formata = formatadores[campo.dataset.formato];
      if (formata) {
        campo.value = formata(campo.value);
      }
    });
  });

  function mostrarConfirmacao(oficio) {
    document.getElementById("oficio").textContent = oficio;
    document.getElementById("tela-formulario").hidden = true;
    document.getElementById("tela-confirmacao").hidden = false;
    window.scrollTo(0, 0);
  }

  Array.prototype.slice.call(document.querySelectorAll(".formulario")).forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();

      var dados = { aba: form.dataset.aba };
      Array.prototype.slice.call(form.querySelectorAll("input, select, textarea")).forEach(function (campo) {
        if (campo.name) {
          dados[campo.name] = campo.value;
        }
      });

      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resposta) {
          var area = form.querySelector(".erros");
          if (resposta.erros && resposta.erros.length) {
            area.innerHTML = resposta.erros.map(function (mensagem) {
              return "<p>" + mensagem + "</p>";
            }).join("");
            return;
          }
          area.innerHTML = "";
          mostrarConfirmacao(resposta.oficio);
        });
    });
  });
})();
