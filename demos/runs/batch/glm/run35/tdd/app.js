(function () {
  "use strict";

  function digitos(texto) {
    return (String(texto).match(/[0-9]/g) || []).join("");
  }

  function milhar(numero) {
    return String(numero).replace(/\B(?=(?:[0-9]{3})+(?![0-9])/g, ".");
  }

  function moeda(texto) {
    var d = digitos(texto);
    var total = d ? parseInt(d, 10) : 0;
    var reais = Math.floor(total / 100);
    var centavos = total % 100;
    return "R$ " + milhar(reais) + "," + (centavos < 10 ? "0" : "") + centavos;
  }

  function cpf(texto) {
    var d = digitos(texto).slice(0, 11);
    var saida = d.slice(0, 3);
    if (d.length > 3) { saida += "." + d.slice(3, 6); }
    if (d.length > 6) { saida += "." + d.slice(6, 9); }
    if (d.length > 9) { saida += "-" + d.slice(9); }
    return saida;
  }

  function cep(texto) {
    var d = digitos(texto).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function data(texto) {
    var d = digitos(texto).slice(0, 8);
    var saida = d.slice(0, 2);
    if (d.length > 2) { saida += "/" + d.slice(2, 4); }
    if (d.length > 4) { saida += "/" + d.slice(4, 8); }
    return saida;
  }

  var MASCARAS = {
    valor: moeda,
    cpf: cpf,
    cep: cep,
    data_nascimento: data
  };

  function configurarAbas() {
    var botoes = Array.prototype.slice.call(document.querySelectorAll(".aba"));
    botoes.forEach(function (botao) {
      botao.addEventListener("click", function () {
        botoes.forEach(function (outro) { outro.classList.remove("ativa"); });
        botao.classList.add("ativa");
        document.querySelectorAll(".painel").forEach(function (painel) {
          painel.classList.remove("ativo");
        });
        var painel = document.getElementById("form-" + botao.getAttribute("data-aba"));
        if (painel) { painel.classList.add("ativo"); }
      });
    });
  }

  function configurarMascaras(form) {
    Object.keys(MASCARAS).forEach(function (nome) {
      var campo = form.elements[nome];
      if (!campo) { return; }
      var aplicar = function () { campo.value = MASCARAS[nome](campo.value); };
      campo.addEventListener("input", aplicar);
      campo.addEventListener("blur", aplicar);
    });
  }

  function mostrarMensagens(form, mensagens) {
    var caixa = form.querySelector(".mensagens");
    caixa.innerHTML = "";
    mensagens.forEach(function (texto) {
      var linha = document.createElement("p");
      linha.textContent = texto;
      caixa.appendChild(linha);
    });
    caixa.hidden = mensagens.length === 0;
  }

  function configurarEnvio(form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(form).forEach(function (valor, chave) { dados[chave] = valor; });
      dados.aba = form.getAttribute("data-aba");
      fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      }).then(function (resposta) {
        return resposta.json();
      }).then(function (resultado) {
        if (resultado.erros && resultado.erros.length) {
          mostrarMensagens(form, resultado.erros);
          return;
        }
        var navegacao = document.querySelector(".abas");
        if (navegacao) { navegacao.hidden = true; }
        document.querySelectorAll(".painel").forEach(function (painel) {
          painel.classList.remove("ativo");
          painel.hidden = true;
        });
        document.getElementById("oficio").textContent = resultado.oficio;
        document.getElementById("confirmacao").hidden = false;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    configurarAbas();
    document.querySelectorAll("form.painel").forEach(function (form) {
      configurarMascaras(form);
      configurarEnvio(form);
    });
  });
})();
