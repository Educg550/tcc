(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");
  var confirmacao = document.getElementById("confirmacao");
  var oficio = document.getElementById("oficio");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      var alvo = aba.getAttribute("data-aba");
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle("ativa", ativa);
        outra.setAttribute("aria-selected", ativa ? "true" : "false");
      });
      formularios.forEach(function (form) {
        form.classList.toggle("ativo", form.getAttribute("data-aba") === alvo);
      });
      confirmacao.hidden = true;
    });
  });

  function soDigitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formataMoeda(valor) {
    var digitos = soDigitos(valor).replace(/^0+(?=\d)/, "");
    if (!digitos) {
      return "";
    }
    var centavos = digitos.slice(-2);
    while (centavos.length < 2) {
      centavos = "0" + centavos;
    }
    var reais = digitos.slice(0, -2) || "0";
    reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formataCpf(valor) {
    var d = soDigitos(valor).slice(0, 11);
    if (d.length <= 3) {
      return d;
    }
    if (d.length <= 6) {
      return d.slice(0, 3) + "." + d.slice(3);
    }
    if (d.length <= 9) {
      return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    }
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function formataCep(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length <= 5) {
      return d;
    }
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formataData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length <= 2) {
      return d;
    }
    if (d.length <= 4) {
      return d.slice(0, 2) + "/" + d.slice(2);
    }
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  var formatadores = {
    moeda: formataMoeda,
    cpf: formataCpf,
    cep: formataCep,
    data: formataData
  };

  document.querySelectorAll("[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      var formatador = formatadores[campo.getAttribute("data-formato")];
      if (formatador) {
        campo.value = formatador(campo.value);
      }
    });
  });

  formularios.forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      dados.aba = form.getAttribute("data-aba");

      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resposta) {
          var erros = form.querySelector(".erros");
          if (resposta.erros && resposta.erros.length) {
            erros.textContent = resposta.erros.join("\n");
            erros.hidden = false;
            return;
          }
          erros.textContent = "";
          erros.hidden = true;
          formularios.forEach(function (outro) {
            outro.classList.remove("ativo");
          });
          oficio.textContent = resposta.oficio;
          confirmacao.hidden = false;
        });
    });
  });
})();
