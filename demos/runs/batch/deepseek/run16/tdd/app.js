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
        painel.classList.toggle("ativo", painel.dataset.aba === aba.dataset.aba);
      });
    });
  });

  function digitos(valor) {
    return (valor || "").replace(/\D/g, "");
  }

  function formatarValor(el) {
    var d = digitos(el.value);
    if (!d) { el.value = ""; return; }
    var reais = parseInt(d, 10) / 100;
    el.value = "R$ " + reais.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatarCPF(el) {
    var d = digitos(el.value).slice(0, 11);
    var saida = d;
    if (d.length > 9) { saida = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9); }
    else if (d.length > 6) { saida = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6); }
    else if (d.length > 3) { saida = d.slice(0, 3) + "." + d.slice(3); }
    el.value = saida;
  }

  function formatarCEP(el) {
    var d = digitos(el.value).slice(0, 8);
    el.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(el) {
    var d = digitos(el.value).slice(0, 8);
    var saida = d;
    if (d.length > 4) { saida = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4); }
    else if (d.length > 2) { saida = d.slice(0, 2) + "/" + d.slice(2); }
    el.value = saida;
  }

  function aoSair(nome, formatador) {
    document.querySelectorAll('input[name="' + nome + '"]').forEach(function (el) {
      el.addEventListener("blur", function () { formatador(el); });
    });
  }

  aoSair("valor", formatarValor);
  aoSair("cpf", formatarCPF);
  aoSair("cep", formatarCEP);
  aoSair("data_nascimento", formatarData);

  function mostrarErros(form, erros) {
    var caixa = form.querySelector(".erros");
    caixa.textContent = "";
    erros.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
  }

  function mostrarConfirmacao(oficio) {
    document.getElementById("area-formularios").hidden = true;
    document.getElementById("confirmacao").hidden = false;
    document.getElementById("oficio").textContent = oficio;
  }

  paineis.forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = { aba: form.dataset.aba };
      form.querySelectorAll("input, select, textarea").forEach(function (el) {
        dados[el.name] = el.value;
      });
      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (resultado) {
          if (resultado.erros && resultado.erros.length) {
            mostrarErros(form, resultado.erros);
          } else {
            mostrarConfirmacao(resultado.oficio);
          }
        });
    });
  });
})();
