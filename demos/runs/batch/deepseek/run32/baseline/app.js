(function () {
  "use strict";

  var formatadores = {
    valor: function (v) {
      var d = v.replace(/\D/g, "");
      if (!d) return "";
      var n = parseInt(d, 10) / 100;
      return "R$ " + n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    cpf: function (v) {
      var d = v.replace(/\D/g, "").slice(0, 11);
      if (d.length <= 3) return d;
      if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
      if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
      return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    },
    cep: function (v) {
      var d = v.replace(/\D/g, "").slice(0, 8);
      if (d.length <= 5) return d;
      return d.slice(0, 5) + "-" + d.slice(5);
    },
    data: function (v) {
      var d = v.replace(/\D/g, "").slice(0, 8);
      if (d.length <= 2) return d;
      if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
      return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    }
  };

  function formatar(campo) {
    var f = formatadores[campo.dataset.format];
    if (f) campo.value = f(campo.value);
  }

  document.querySelectorAll("[data-format]").forEach(function (campo) {
    campo.addEventListener("blur", function () { formatar(campo); });
  });

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("ativa"); });
      botao.classList.add("ativa");
      document.querySelectorAll(".formulario").forEach(function (f) { f.classList.remove("ativo"); });
      document.getElementById("form-" + botao.dataset.aba).classList.add("ativo");
    });
  });

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();

      form.querySelectorAll("[data-format]").forEach(formatar);

      var dados = { aba: form.dataset.aba };
      form.querySelectorAll("[name]").forEach(function (el) { dados[el.name] = el.value; });

      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (json) {
          var caixa = document.getElementById("erros-" + form.dataset.aba);
          caixa.textContent = "";
          if (json.erros && json.erros.length) {
            json.erros.forEach(function (msg) {
              var d = document.createElement("div");
              d.textContent = msg;
              caixa.appendChild(d);
            });
            return;
          }
          document.querySelector(".abas").classList.add("escondido");
          document.querySelectorAll(".formulario").forEach(function (f) { f.classList.add("escondido"); });
          document.getElementById("oficio").textContent = json.oficio;
          document.getElementById("confirmacao").classList.remove("escondido");
        });
    });
  });
})();
