(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var paineis = document.querySelectorAll("[data-painel]");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      paineis.forEach(function (painel) {
        painel.classList.toggle("ativo", painel.dataset.painel === aba.dataset.aba);
      });
    });
  });

  function digitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formatarMoeda(valor) {
    var d = digitos(valor);
    if (!d) return "";
    var numero = parseInt(d, 10) / 100;
    return "R$ " + numero.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function formatarCPF(valor) {
    var d = digitos(valor).slice(0, 11);
    var saida = d.slice(0, 3);
    if (d.length > 3) saida += "." + d.slice(3, 6);
    if (d.length > 6) saida += "." + d.slice(6, 9);
    if (d.length > 9) saida += "-" + d.slice(9, 11);
    return saida;
  }

  function formatarCEP(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(valor) {
    var d = digitos(valor).slice(0, 8);
    var saida = d.slice(0, 2);
    if (d.length > 2) saida += "/" + d.slice(2, 4);
    if (d.length > 4) saida += "/" + d.slice(4, 8);
    return saida;
  }

  var formatadores = {
    moeda: formatarMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data: formatarData
  };

  document.querySelectorAll("[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      var formatar = formatadores[campo.dataset.formato];
      if (formatar) campo.value = formatar(campo.value);
    });
  });

  function coletar(formulario) {
    var dados = {};
    new FormData(formulario).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    return dados;
  }

  function mostrarErros(aba, mensagens) {
    var caixa = document.getElementById("erros-" + aba);
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function mostrarConfirmacao(oficio) {
    document.querySelector(".abas").hidden = true;
    paineis.forEach(function (painel) {
      painel.hidden = true;
    });
    document.getElementById("oficio").textContent = oficio;
    var confirmacao = document.getElementById("confirmacao");
    confirmacao.classList.add("ativo");
    confirmacao.hidden = false;
  }

  document.querySelectorAll("form").forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var aba = formulario.dataset.aba;
      var dados = coletar(formulario);
      dados.aba = aba;

      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.text().then(function (texto) {
            return { ok: resposta.ok, texto: texto };
          });
        })
        .then(function (resultado) {
          if (resultado.ok) {
            mostrarConfirmacao(resultado.texto);
            return;
          }
          var mensagens = resultado.texto.split("\n").filter(function (linha) {
            return linha.trim() !== "";
          });
          mostrarErros(aba, mensagens);
        });
    });
  });
})();
