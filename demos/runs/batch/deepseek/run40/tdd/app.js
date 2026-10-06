(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* Abas                                                                */
  /* ------------------------------------------------------------------ */
  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (outra) {
        outra.classList.remove("ativa");
      });
      document.querySelectorAll(".formulario").forEach(function (form) {
        form.classList.remove("ativa");
      });
      aba.classList.add("ativa");
      var alvo = document.getElementById("form-" + aba.dataset.aba);
      if (alvo) alvo.classList.add("ativa");
    });
  });

  /* ------------------------------------------------------------------ */
  /* Formatação dos campos                                               */
  /* ------------------------------------------------------------------ */
  function formatarValor(valor) {
    var digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    var centavos = parseInt(digitos, 10);
    return (
      "R$ " +
      (centavos / 100).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  function formatarCPF(valor) {
    return valor
      .replace(/\D/g, "")
      .slice(0, 11)
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  }

  function formatarCEP(valor) {
    return valor.replace(/\D/g, "").slice(0, 8).replace(/(\d{5})(\d)/, "$1-$2");
  }

  function formatarData(valor) {
    return valor
      .replace(/\D/g, "")
      .slice(0, 8)
      .replace(/(\d{2})(\d)/, "$1/$2")
      .replace(/(\d{2})(\d)/, "$1/$2");
  }

  var formatadores = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData,
  };

  function formatarTudo(form) {
    Object.keys(formatadores).forEach(function (campo) {
      var el = form.querySelector('[name="' + campo + '"]');
      if (el) el.value = formatadores[campo](el.value);
    });
  }

  /* ------------------------------------------------------------------ */
  /* Envio                                                               */
  /* ------------------------------------------------------------------ */
  function mostrarErros(form, mensagens) {
    var box = form.querySelector(".erros");
    box.innerHTML = "";
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("div");
      linha.textContent = mensagem;
      box.appendChild(linha);
    });
    box.hidden = false;
  }

  function mostrarConfirmacao(oficio) {
    document.getElementById("oficio").textContent = oficio;
    document.querySelectorAll(".formulario").forEach(function (form) {
      form.classList.remove("ativa");
    });
    document.querySelector(".abas").hidden = true;
    document.getElementById("confirmacao").hidden = false;
  }

  function enviar(form) {
    var dados = {};
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });

    fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: form.dataset.aba, dados: dados }),
    })
      .then(function (resposta) {
        return resposta.json();
      })
      .then(function (resposta) {
        var box = form.querySelector(".erros");
        if (resposta.erros && resposta.erros.length) {
          mostrarErros(form, resposta.erros);
        } else {
          box.hidden = true;
          mostrarConfirmacao(resposta.oficio);
        }
      })
      .catch(function () {
        mostrarErros(form, [
          "Não foi possível enviar a solicitação. Tente novamente.",
        ]);
      });
  }

  document.querySelectorAll("form").forEach(function (form) {
    Object.keys(formatadores).forEach(function (campo) {
      var el = form.querySelector('[name="' + campo + '"]');
      if (!el) return;
      el.addEventListener("blur", function () {
        el.value = formatadores[campo](el.value);
      });
    });

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      formatarTudo(form);
      enviar(form);
    });
  });
})();
