(function () {
  function digits(valor) {
    return (valor || "").replace(/\D/g, "");
  }

  function formataValor(valor) {
    var d = digits(valor).replace(/^0+/, "");
    if (!d) return "";
    if (d.length < 3) d = d.padStart(3, "0");
    var centavos = d.slice(-2);
    var reais = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formataCPF(valor) {
    var d = digits(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  function formataCEP(valor) {
    var d = digits(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formataData(valor) {
    var d = digits(valor).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var FORMATADORES = {
    valor_solicitado: formataValor,
    cpf: formataCPF,
    cep: formataCEP,
    data_nascimento: formataData,
  };

  function formatarCampos() {
    document.querySelectorAll("input[name]").forEach(function (input) {
      var formatador = FORMATADORES[input.name];
      if (formatador && input.value) {
        input.value = formatador(input.value);
      }
    });
  }

  document.querySelectorAll("input[name]").forEach(function (input) {
    var formatador = FORMATADORES[input.name];
    if (!formatador) return;
    input.addEventListener("blur", function () {
      input.value = formatador(input.value);
    });
  });

  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.addEventListener("click", function () {
      var alvo = aba.dataset.aba;
      document.querySelectorAll(".aba").forEach(function (outra) {
        outra.classList.toggle("active", outra.dataset.aba === alvo);
      });
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.classList.toggle("ativo", painel.dataset.painel === alvo);
      });
    });
  });

  function coletar(form) {
    var dados = {};
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    return dados;
  }

  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      formatarCampos();
      var caixaErros = form.parentElement.querySelector("[data-erros]");
      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(coletar(form)),
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resposta) {
          if (resposta.erros && resposta.erros.length) {
            caixaErros.textContent = resposta.erros.join("\n");
            caixaErros.hidden = false;
            return;
          }
          caixaErros.hidden = true;
          caixaErros.textContent = "";
          document.getElementById("oficio").textContent = resposta.oficio;
          document.getElementById("confirmacao").hidden = false;
          document.body.classList.add("concluido");
        });
    });
  });
})();
