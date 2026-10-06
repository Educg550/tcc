(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");

  function trocarAba(nome) {
    abas.forEach(function (b) {
      var ativa = b.dataset.aba === nome;
      b.classList.toggle("ativa", ativa);
      b.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    document.querySelectorAll(".painel-form").forEach(function (p) {
      p.classList.toggle("ativo", p.dataset.aba === nome);
    });
  }

  abas.forEach(function (b) {
    b.addEventListener("click", function () {
      trocarAba(b.dataset.aba);
    });
  });

  function soDigitos(v) {
    return (v || "").replace(/\D/g, "");
  }

  function formatoMoeda(v) {
    var d = soDigitos(v);
    if (!d) return "";
    var cents = parseInt(d, 10);
    var reais = Math.floor(cents / 100);
    var cent = cents % 100;
    return "R$ " + reais.toLocaleString("pt-BR") + "," + String(cent).padStart(2, "0");
  }

  function formatoCPF(v) {
    var d = soDigitos(v).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  function formatoCEP(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formatoData(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  document.querySelectorAll('[data-mask="moeda"]').forEach(function (el) {
    el.addEventListener("input", function () {
      el.value = formatoMoeda(el.value);
    });
    el.addEventListener("blur", function () {
      el.value = formatoMoeda(el.value);
    });
  });

  document.querySelectorAll('[data-mask="cpf"]').forEach(function (el) {
    el.addEventListener("blur", function () {
      el.value = formatoCPF(el.value);
    });
  });

  document.querySelectorAll('[data-mask="cep"]').forEach(function (el) {
    el.addEventListener("blur", function () {
      el.value = formatoCEP(el.value);
    });
  });

  document.querySelectorAll('[data-mask="data"]').forEach(function (el) {
    el.addEventListener("blur", function () {
      el.value = formatoData(el.value);
    });
  });

  function mostrarResultado(form, resposta) {
    var caixa = form.querySelector(".mensagens-erro");
    if (resposta.erros && resposta.erros.length) {
      caixa.innerHTML = resposta.erros
        .map(function (e) {
          return "<p></p>";
        })
        .join("");
      var itens = caixa.querySelectorAll("p");
      resposta.erros.forEach(function (e, i) {
        itens[i].textContent = e;
      });
      caixa.hidden = false;
      return;
    }
    caixa.hidden = true;
    caixa.innerHTML = "";
    document.getElementById("oficio").textContent = resposta.oficio || "";
    document.getElementById("pagina-formulario").hidden = true;
    document.getElementById("pagina-confirmacao").hidden = false;
  }

  document.querySelectorAll(".form-solicitacao").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var dados = {};
      form.querySelectorAll("[name]").forEach(function (el) {
        dados[el.name] = el.value.trim();
      });
      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aba: form.dataset.aba, dados: dados }),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (resposta) {
          mostrarResultado(form, resposta);
        });
    });
  });
})();
