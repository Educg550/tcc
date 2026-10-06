(function () {
  "use strict";

  var formatadores = {
    valor: function (texto) {
      var digitos = texto.replace(/\D/g, "");
      if (!digitos) return "";
      var numero = parseInt(digitos, 10) / 100;
      return "R$ " + numero.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    cpf: function (texto) {
      var d = texto.replace(/\D/g, "").slice(0, 11);
      if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
      if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
      if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
      return d;
    },
    cep: function (texto) {
      var d = texto.replace(/\D/g, "").slice(0, 8);
      return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
    },
    data: function (texto) {
      var d = texto.replace(/\D/g, "").slice(0, 8);
      if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
      if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
      return d;
    }
  };

  document.querySelectorAll("[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = formatadores[campo.dataset.formato](campo.value);
    });
  });

  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      formularios.forEach(function (form) {
        form.classList.toggle("ativo", form.id === "form-" + aba.dataset.aba);
      });
    });
  });

  formularios.forEach(function (form) {
    form.querySelector("form").addEventListener("submit", function (evento) {
      evento.preventDefault();

      var dados = { aba: form.dataset.aba };
      form.querySelectorAll("[name]").forEach(function (campo) {
        dados[campo.name] = campo.value.trim();
      });

      fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (corpo) {
          var erros = form.querySelector(".erros");
          if (corpo.erros && corpo.erros.length) {
            erros.textContent = corpo.erros.join("\n");
            erros.hidden = false;
            return;
          }
          mostrarConfirmacao(corpo.oficio);
        });
    });
  });

  function mostrarConfirmacao(oficio) {
    document.querySelector(".abas").hidden = true;
    formularios.forEach(function (form) { form.hidden = true; });
    document.getElementById("oficio").textContent = oficio;
    document.getElementById("confirmacao").hidden = false;
  }
})();
