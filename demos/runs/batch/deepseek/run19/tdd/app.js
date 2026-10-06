(function () {
  "use strict";

  function soDigitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formataValor(valor) {
    var d = soDigitos(valor).replace(/^0+(?=\d)/, "");
    if (!d) return "";
    d = d.padStart(3, "0");
    var centavos = d.slice(-2);
    var inteiros = d.slice(0, -2).replace(/^0+(?=\d)/, "");
    inteiros = inteiros.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + inteiros + "," + centavos;
  }

  function formataCpf(valor) {
    var d = soDigitos(valor).slice(0, 11);
    var saida = d.slice(0, 3);
    if (d.length > 3) saida += "." + d.slice(3, 6);
    if (d.length > 6) saida += "." + d.slice(6, 9);
    if (d.length > 9) saida += "-" + d.slice(9, 11);
    return saida;
  }

  function formataCep(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formataData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    var saida = d.slice(0, 2);
    if (d.length > 2) saida += "/" + d.slice(2, 4);
    if (d.length > 4) saida += "/" + d.slice(4, 8);
    return saida;
  }

  var FORMATOS = {
    valor: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data: formataData
  };

  document.querySelectorAll("input[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = FORMATOS[campo.dataset.formato](campo.value);
    });
  });

  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");

  abas.forEach(function (botao) {
    botao.addEventListener("click", function () {
      var alvo = botao.dataset.aba;
      abas.forEach(function (outra) {
        var ativa = outra === botao;
        outra.classList.toggle("ativa", ativa);
        outra.setAttribute("aria-selected", ativa ? "true" : "false");
      });
      formularios.forEach(function (form) {
        form.classList.toggle("ativo", form.dataset.aba === alvo);
      });
    });
  });

  formularios.forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();

      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      dados.aba = form.dataset.aba;

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          var caixa = form.querySelector(".erros");

          if (resultado.erros && resultado.erros.length) {
            caixa.innerHTML = "";
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement("p");
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            caixa.hidden = false;
            return;
          }

          caixa.hidden = true;
          document.getElementById("oficio").textContent = resultado.oficio;
          document.querySelector(".abas").hidden = true;
          form.classList.remove("ativo");
          document.getElementById("confirmacao").hidden = false;
        });
    });
  });
})();
