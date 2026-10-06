(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var paineis = document.querySelectorAll(".painel");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      paineis.forEach(function (painel) {
        painel.classList.toggle("ativa", painel.id === "painel-" + aba.dataset.aba);
      });
    });
  });

  function digitos(valor) {
    return (valor || "").replace(/\D/g, "");
  }

  function formatarValor(valor) {
    var d = digitos(valor).replace(/^0+/, "");
    if (!d) return "";
    d = d.padStart(3, "0");
    var centavos = d.slice(-2);
    var reais = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formatarCPF(valor) {
    var d = digitos(valor).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function formatarCEP(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formatarData(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  var formatadores = {
    valor_solicitado: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData,
  };

  document.querySelectorAll("input[name]").forEach(function (campo) {
    var formatar = formatadores[campo.name];
    if (formatar) {
      campo.addEventListener("blur", function () {
        campo.value = formatar(campo.value);
      });
    }
  });

  function coletar(formulario) {
    var dados = {};
    formulario.querySelectorAll("[name]").forEach(function (campo) {
      dados[campo.name] = campo.value.trim();
    });
    return dados;
  }

  function mostrarErros(caixa, mensagens) {
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function mostrarConfirmacao(corpo) {
    document.getElementById("tela-formularios").hidden = true;
    document.getElementById("titulo-confirmacao").textContent = corpo.titulo;
    document.getElementById("oficio").textContent = corpo.oficio;
    document.getElementById("confirmacao").hidden = false;
  }

  document.querySelectorAll("form").forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var caixa = formulario.querySelector(".erros");
      caixa.hidden = true;
      caixa.textContent = "";

      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(coletar(formulario)),
      })
        .then(function (resposta) {
          return resposta.json().then(function (corpo) {
            return { ok: resposta.ok, corpo: corpo };
          });
        })
        .then(function (resultado) {
          if (resultado.ok) {
            mostrarConfirmacao(resultado.corpo);
          } else {
            mostrarErros(caixa, resultado.corpo.erros || []);
          }
        });
    });
  });
})();
