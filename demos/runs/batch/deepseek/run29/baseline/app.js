(function () {
  "use strict";

  function formataValor(valor) {
    var digitos = valor.replace(/\D/g, "").replace(/^0+/, "");
    if (!digitos) return "";
    digitos = digitos.padStart(3, "0");
    var centavos = digitos.slice(-2);
    var reais = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formataCpf(valor) {
    var d = valor.replace(/\D/g, "").slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  function formataCep(valor) {
    var d = valor.replace(/\D/g, "").slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formataData(valor) {
    var d = valor.replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var formatadores = {
    valor_solicitado: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data_nascimento: formataData
  };

  function formataCampos(form) {
    form.querySelectorAll("input").forEach(function (campo) {
      var formatador = formatadores[campo.name];
      if (formatador) campo.value = formatador(campo.value);
    });
  }

  document.querySelectorAll("input").forEach(function (campo) {
    var formatador = formatadores[campo.name];
    if (!formatador) return;
    campo.addEventListener("blur", function () {
      campo.value = formatador(campo.value);
    });
  });

  var abas = document.querySelectorAll(".aba");
  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle("ativa", ativa);
        outra.setAttribute("aria-selected", ativa ? "true" : "false");
      });
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.classList.toggle("oculto", painel.id !== "painel-" + aba.dataset.aba);
      });
    });
  });

  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var tipo = form.dataset.tipo;
      formataCampos(form);

      var dados = { tipo: tipo };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });

      var caixa = document.getElementById("erros-" + tipo);

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          if (resultado.erros && resultado.erros.length) {
            caixa.innerHTML = "";
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement("div");
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            return;
          }
          caixa.innerHTML = "";
          document.querySelector(".abas").classList.add("oculto");
          document.querySelectorAll(".painel").forEach(function (painel) {
            painel.classList.add("oculto");
          });
          document.getElementById("confirmacao").classList.remove("oculto");
          document.getElementById("oficio").textContent = resultado.oficio;
        });
    });
  });
})();
