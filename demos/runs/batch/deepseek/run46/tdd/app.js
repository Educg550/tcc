(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var paineis = document.querySelectorAll(".painel");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      var alvo = aba.dataset.aba;
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      paineis.forEach(function (painel) {
        painel.classList.toggle("ativa", painel.id === "painel-" + alvo);
      });
    });
  });

  var formatos = {
    moeda: function (valor) {
      var digitos = valor.replace(/\D/g, "");
      if (!digitos) return "";
      var centavos = parseInt(digitos, 10);
      var reais = Math.floor(centavos / 100);
      var cent = String(centavos % 100).padStart(2, "0");
      return "R$ " + reais.toLocaleString("pt-BR") + "," + cent;
    },
    cpf: function (valor) {
      var d = valor.replace(/\D/g, "").slice(0, 11);
      if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
      if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
      if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
      return d;
    },
    cep: function (valor) {
      var d = valor.replace(/\D/g, "").slice(0, 8);
      return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
    },
    data: function (valor) {
      var d = valor.replace(/\D/g, "").slice(0, 8);
      if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
      if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
      return d;
    },
  };

  document.querySelectorAll("[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = formatos[campo.dataset.formato](campo.value);
    });
  });

  function enviar(aba) {
    var form = document.getElementById("form-" + aba);
    var dados = {};
    new FormData(form).forEach(function (valor, nome) {
      dados[nome] = valor;
    });

    fetch("/solicitar/" + aba, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then(function (resposta) {
        return resposta.json().then(function (corpo) {
          return { ok: resposta.ok, corpo: corpo };
        });
      })
      .then(function (resultado) {
        var erros = document.getElementById("erros-" + aba);
        if (!resultado.ok) {
          erros.innerHTML = "";
          (resultado.corpo.erros || []).forEach(function (mensagem) {
            var linha = document.createElement("p");
            linha.textContent = mensagem;
            erros.appendChild(linha);
          });
          erros.hidden = false;
          return;
        }
        erros.hidden = true;
        document.getElementById("formularios").hidden = true;
        document.querySelector(".abas").hidden = true;
        document.getElementById("oficio").textContent = resultado.corpo.oficio;
        document.getElementById("confirmacao").hidden = false;
      });
  }

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form.id.replace("form-", ""));
    });
  });
})();
