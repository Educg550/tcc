(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      formularios.forEach(function (form) {
        form.classList.toggle("ativo", form.dataset.aba === aba.dataset.aba);
      });
    });
  });

  function somenteDigitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formatarValor(campo) {
    var digitos = somenteDigitos(campo.value);
    if (!digitos) {
      campo.value = "";
      return;
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = String(centavos % 100).padStart(2, "0");
    campo.value = "R$ " + reais.toLocaleString("pt-BR") + "," + resto;
  }

  function formatarCPF(campo) {
    var d = somenteDigitos(campo.value).slice(0, 11);
    var v = d;
    if (d.length > 9) {
      v = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    } else if (d.length > 6) {
      v = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    } else if (d.length > 3) {
      v = d.slice(0, 3) + "." + d.slice(3);
    }
    campo.value = v;
  }

  function formatarCEP(campo) {
    var d = somenteDigitos(campo.value).slice(0, 8);
    campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(campo) {
    var d = somenteDigitos(campo.value).slice(0, 8);
    var v = d;
    if (d.length > 4) {
      v = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    } else if (d.length > 2) {
      v = d.slice(0, 2) + "/" + d.slice(2);
    }
    campo.value = v;
  }

  function formatarCampo(campo) {
    var tipo = campo.dataset.format;
    if (tipo === "valor") formatarValor(campo);
    else if (tipo === "cpf") formatarCPF(campo);
    else if (tipo === "cep") formatarCEP(campo);
    else if (tipo === "data") formatarData(campo);
  }

  document.querySelectorAll("[data-format]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      formatarCampo(campo);
    });
  });

  formularios.forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();

      form.querySelectorAll("[data-format]").forEach(formatarCampo);

      var dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = String(valor).trim();
      });

      fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          if (resultado.ok) {
            document.getElementById("formularios").hidden = true;
            document.getElementById("confirmacao").hidden = false;
            document.getElementById("oficio").textContent = resultado.oficio;
            window.scrollTo(0, 0);
            return;
          }
          var alvo = form.querySelector(".erros");
          alvo.replaceChildren.apply(
            alvo,
            resultado.erros.map(function (mensagem) {
              var p = document.createElement("p");
              p.textContent = mensagem;
              return p;
            })
          );
        });
    });
  });
})();
