(function () {
  "use strict";

  function digitos(v) { return (v || "").replace(/[^0-9]/g, ""); }

  function formatarValor(input) {
    var d = digitos(input.value);
    if (!d) { input.value = ""; return; }
    var centavos = parseInt(d, 10);
    input.value = "R$ " + (centavos / 100).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatarCPF(input) {
    var d = digitos(input.value).slice(0, 11);
    if (d.length > 9) {
      input.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    } else if (d.length > 6) {
      input.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    } else if (d.length > 3) {
      input.value = d.slice(0, 3) + "." + d.slice(3);
    } else {
      input.value = d;
    }
  }

  function formatarCEP(input) {
    var d = digitos(input.value).slice(0, 8);
    input.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(input) {
    var d = digitos(input.value).slice(0, 8);
    if (d.length > 4) {
      input.value = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    } else if (d.length > 2) {
      input.value = d.slice(0, 2) + "/" + d.slice(2);
    } else {
      input.value = d;
    }
  }

  function selecionarAba(nome) {
    document.querySelectorAll(".aba").forEach(function (b) {
      var ativa = b.dataset.aba === nome;
      b.classList.toggle("ativa", ativa);
      b.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    document.querySelectorAll(".painel").forEach(function (p) {
      p.classList.toggle("ativo", p.dataset.aba === nome);
    });
  }

  function mostrarErros(form, erros) {
    var caixa = form.querySelector(".erros");
    caixa.textContent = "";
    erros.forEach(function (m) {
      var linha = document.createElement("div");
      linha.textContent = m;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function limparErros(form) {
    var caixa = form.querySelector(".erros");
    caixa.hidden = true;
    caixa.textContent = "";
  }

  function montarDados(form) {
    var dados = {};
    new FormData(form).forEach(function (valor, chave) { dados[chave] = valor; });
    var campoValor = form.querySelector('[name="valor"]');
    if (campoValor) { dados.valor = digitos(campoValor.value); }
    return dados;
  }

  function enviar(form) {
    return function (evento) {
      evento.preventDefault();
      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(montarDados(form))
      })
        .then(function (r) { return r.json(); })
        .then(function (corpo) {
          var erros = corpo.erros || [];
          if (erros.length) { mostrarErros(form, erros); return; }
          limparErros(form);
          document.querySelector(".abas").hidden = true;
          document.querySelector(".formularios").hidden = true;
          var confirmacao = document.querySelector(".confirmacao");
          confirmacao.querySelector(".oficio").textContent = corpo.oficio;
          confirmacao.hidden = false;
        });
    };
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".aba").forEach(function (b) {
      b.addEventListener("click", function () { selecionarAba(b.dataset.aba); });
    });
    document.querySelectorAll("form.solicitacao").forEach(function (form) {
      var valor = form.querySelector('[name="valor"]');
      var cpf = form.querySelector('[name="cpf"]');
      var cep = form.querySelector('[name="cep"]');
      var nasc = form.querySelector('[name="data_nascimento"]');
      if (valor) valor.addEventListener("blur", function () { formatarValor(valor); });
      if (cpf) cpf.addEventListener("blur", function () { formatarCPF(cpf); });
      if (cep) cep.addEventListener("blur", function () { formatarCEP(cep); });
      if (nasc) nasc.addEventListener("blur", function () { formatarData(nasc); });
      form.addEventListener("submit", enviar(form));
    });
  });
})();
