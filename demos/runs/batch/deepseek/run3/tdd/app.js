(function () {
  "use strict";

  function formatarMoeda(valor) {
    var digitos = String(valor).replace(/\D/g, "").replace(/^0+/, "");
    if (digitos === "") return "";
    digitos = digitos.padStart(3, "0");
    var centavos = digitos.slice(-2);
    var reais = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formatarCPF(valor) {
    var d = String(valor).replace(/\D/g, "").slice(0, 11);
    if (d.length > 9) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, "$1.$2.$3-$4");
    if (d.length > 6) return d.replace(/(\d{3})(\d{3})(\d{0,3})/, "$1.$2.$3");
    if (d.length > 3) return d.replace(/(\d{3})(\d{0,3})/, "$1.$2");
    return d;
  }

  function formatarCEP(valor) {
    var d = String(valor).replace(/\D/g, "").slice(0, 8);
    if (d.length > 5) return d.replace(/(\d{5})(\d{0,3})/, "$1-$2");
    return d;
  }

  function formatarData(valor) {
    var d = String(valor).replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return d.replace(/(\d{2})(\d{2})(\d{0,4})/, "$1/$2/$3");
    if (d.length > 2) return d.replace(/(\d{2})(\d{0,2})/, "$1/$2");
    return d;
  }

  var formatadores = {
    "js-moeda": formatarMoeda,
    "js-cpf": formatarCPF,
    "js-cep": formatarCEP,
    "js-data": formatarData,
  };

  Object.keys(formatadores).forEach(function (classe) {
    document.querySelectorAll("." + classe).forEach(function (campo) {
      campo.addEventListener("blur", function () {
        campo.value = formatadores[classe](campo.value);
      });
    });
  });

  function aplicarFormatacao(form) {
    Object.keys(formatadores).forEach(function (classe) {
      form.querySelectorAll("." + classe).forEach(function (campo) {
        campo.value = formatadores[classe](campo.value);
      });
    });
  }

  var abas = document.querySelectorAll(".aba");
  var paineis = document.querySelectorAll(".painel");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      paineis.forEach(function (painel) {
        painel.classList.toggle("oculto", painel.id !== "painel-" + aba.dataset.aba);
      });
    });
  });

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      aplicarFormatacao(form);

      var dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });

      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          var caixaErros = document.getElementById("erros-" + form.dataset.aba);
          caixaErros.textContent = "";

          if (resultado.erros && resultado.erros.length) {
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement("p");
              linha.textContent = mensagem;
              caixaErros.appendChild(linha);
            });
            caixaErros.classList.remove("oculto");
            return;
          }

          caixaErros.classList.add("oculto");
          document.querySelectorAll(".painel").forEach(function (painel) {
            painel.classList.add("oculto");
          });
          document.querySelector(".abas").classList.add("oculto");
          document.getElementById("oficio").textContent = resultado.oficio;
          document.getElementById("confirmacao").classList.remove("oculto");
        });
    });
  });
})();
