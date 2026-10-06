(function () {
  "use strict";

  function formatarMilhar(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function formatarValor(el) {
    var d = el.value.replace(/\D/g, "");
    if (!d) { el.value = ""; return; }
    var centavos = parseInt(d, 10);
    var reais = Math.floor(centavos / 100);
    var cents = centavos % 100;
    el.value = "R$ " + formatarMilhar(reais) + "," + String(cents).padStart(2, "0");
  }

  function formatarCPF(el) {
    var d = el.value.replace(/\D/g, "").slice(0, 11);
    el.value = d
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
  }

  function formatarCEP(el) {
    var d = el.value.replace(/\D/g, "").slice(0, 8);
    el.value = d.replace(/^(\d{5})(\d)/, "$1-$2");
  }

  function formatarData(el) {
    var d = el.value.replace(/\D/g, "").slice(0, 8);
    el.value = d
      .replace(/^(\d{2})(\d)/, "$1/$2")
      .replace(/^(\d{2})\/(\d{2})(\d)/, "$1/$2/$3");
  }

  var formatadores = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  function mostrarOficio(texto) {
    document.querySelector(".abas").hidden = true;
    document.querySelectorAll(".painel").forEach(function (p) { p.hidden = true; });
    document.getElementById("oficio").textContent = texto;
    document.getElementById("confirmacao").hidden = false;
  }

  function enviar(dados, form) {
    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    })
      .then(function (r) { return r.json(); })
      .then(function (resposta) {
        var caixa = form.parentElement.querySelector(".erros");
        if (resposta.erros && resposta.erros.length) {
          caixa.textContent = resposta.erros.join("\n");
          caixa.hidden = false;
        } else {
          caixa.hidden = true;
          mostrarOficio(resposta.oficio);
        }
      });
  }

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.querySelectorAll("[name]").forEach(function (el) {
      var f = formatadores[el.name];
      if (f) el.addEventListener("blur", function () { f(el); });
    });

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var dados = { aba: form.dataset.form };
      form.querySelectorAll("[name]").forEach(function (el) {
        var f = formatadores[el.name];
        if (f) f(el);
        dados[el.name] = el.value;
      });
      enviar(dados, form);
    });
  });

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (b) {
        b.classList.toggle("ativa", b === botao);
      });
      document.querySelectorAll(".painel").forEach(function (p) {
        p.classList.toggle("ativo", p.dataset.painel === botao.dataset.aba);
      });
    });
  });
})();
