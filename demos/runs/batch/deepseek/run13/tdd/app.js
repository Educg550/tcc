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
        painel.classList.toggle("ativo", painel.id === "painel-" + aba.dataset.aba);
      });
    });
  });

  function digitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formatarValor(valor) {
    var d = digitos(valor).replace(/^0+(?=\d)/, "");
    if (!d) {
      return "";
    }
    d = d.padStart(3, "0");
    var reais = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + d.slice(-2);
  }

  function formatarCPF(valor) {
    var d = digitos(valor).slice(0, 11);
    return d
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d{1,2})$/, ".$1-$2");
  }

  function formatarCEP(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(valor) {
    var d = digitos(valor).slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + "/" + d.slice(2);
    }
    return d;
  }

  var MASCARAS = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  function aplicarMascaras(form) {
    Object.keys(MASCARAS).forEach(function (nome) {
      var campo = form.elements[nome];
      if (campo) {
        campo.value = MASCARAS[nome](campo.value);
      }
    });
  }

  function mostrarConfirmacao(oficio) {
    document.querySelector(".abas").hidden = true;
    paineis.forEach(function (painel) {
      painel.hidden = true;
    });
    var secao = document.getElementById("confirmacao");
    secao.hidden = false;
    secao.querySelector(".oficio").textContent = oficio;
  }

  document.querySelectorAll("form.formulario").forEach(function (form) {
    Object.keys(MASCARAS).forEach(function (nome) {
      var campo = form.elements[nome];
      if (!campo) {
        return;
      }
      campo.addEventListener("blur", function () {
        campo.value = MASCARAS[nome](campo.value);
      });
    });

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      aplicarMascaras(form);

      var corpo = new URLSearchParams(new FormData(form));
      corpo.set("aba", form.dataset.aba);

      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: corpo.toString()
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (dados) {
          var caixa = form.querySelector(".erros");
          if (dados.erros && dados.erros.length) {
            caixa.hidden = false;
            caixa.innerHTML =
              "<ul>" +
              dados.erros
                .map(function (erro) {
                  return "<li>" + erro + "</li>";
                })
                .join("") +
              "</ul>";
            return;
          }
          caixa.hidden = true;
          mostrarConfirmacao(dados.oficio);
        });
    });
  });
})();
