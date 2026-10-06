(function () {
  "use strict";

  function trocarAba(nome) {
    document.querySelectorAll(".aba").forEach(function (botao) {
      var ativa = botao.dataset.aba === nome;
      botao.classList.toggle("ativa", ativa);
      botao.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    document.querySelectorAll(".painel").forEach(function (painel) {
      painel.hidden = painel.dataset.aba !== nome;
    });
  }

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      trocarAba(botao.dataset.aba);
    });
  });

  function somenteDigitos(valor) {
    return (valor.match(/\d/g) || []).join("");
  }

  function formatarValor(valor) {
    var digitos = somenteDigitos(valor);
    if (!digitos) return "";
    var centavos = parseInt(digitos, 10);
    var reais = (centavos / 100).toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return "R$ " + reais;
  }

  function formatarCPF(valor) {
    var digitos = somenteDigitos(valor).slice(0, 11);
    var saida = digitos.slice(0, 3);
    if (digitos.length > 3) saida += "." + digitos.slice(3, 6);
    if (digitos.length > 6) saida += "." + digitos.slice(6, 9);
    if (digitos.length > 9) saida += "-" + digitos.slice(9, 11);
    return saida;
  }

  function formatarCEP(valor) {
    var digitos = somenteDigitos(valor).slice(0, 8);
    if (digitos.length <= 5) return digitos;
    return digitos.slice(0, 5) + "-" + digitos.slice(5);
  }

  function formatarData(valor) {
    var digitos = somenteDigitos(valor).slice(0, 8);
    if (digitos.length <= 2) return digitos;
    if (digitos.length <= 4) return digitos.slice(0, 2) + "/" + digitos.slice(2);
    return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
  }

  var MASCARAS = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData,
  };

  function aplicarMascara(campo) {
    var formatadora = MASCARAS[campo.dataset.mascara];
    if (formatadora) campo.value = formatadora(campo.value);
  }

  function mostrarErros(formulario, mensagens) {
    var caixa = formulario.querySelector(".erros");
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function mostrarOficio(texto) {
    document.querySelector(".abas").hidden = true;
    document.querySelectorAll(".painel").forEach(function (painel) {
      painel.hidden = true;
    });
    document.getElementById("oficio").textContent = texto;
    document.getElementById("confirmacao").hidden = false;
  }

  document.querySelectorAll(".formulario").forEach(function (formulario) {
    formulario.addEventListener("focusout", function (evento) {
      if (evento.target.dataset && evento.target.dataset.mascara) {
        aplicarMascara(evento.target);
      }
    });

    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      formulario.querySelectorAll("[data-mascara]").forEach(aplicarMascara);

      var dados = Object.fromEntries(new FormData(formulario).entries());
      dados.aba = formulario.dataset.aba;

      fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          if (resultado.erros && resultado.erros.length) {
            mostrarErros(formulario, resultado.erros);
            return;
          }
          formulario.querySelector(".erros").hidden = true;
          mostrarOficio(resultado.oficio);
        });
    });
  });
})();
