(function () {
  "use strict";

  var FORMATADORES = {
    valor_solicitado: formatarMoeda,
    cpf: formatarCpf,
    cep: formatarCep,
    data_nascimento: formatarData
  };

  function digitos(valor) {
    return (valor || "").replace(/\D+/g, "");
  }

  function formatarMoeda(valor) {
    var d = digitos(valor).replace(/^0+(?=\d)/, "");
    if (!d) return "";
    var centavos = d.slice(-2).padStart(2, "0");
    var inteiros = (d.slice(0, -2) || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + inteiros + "," + centavos;
  }

  function formatarCpf(valor) {
    var d = digitos(valor).slice(0, 11);
    var saida = d.slice(0, 3);
    if (d.length > 3) saida += "." + d.slice(3, 6);
    if (d.length > 6) saida += "." + d.slice(6, 9);
    if (d.length > 9) saida += "-" + d.slice(9, 11);
    return saida;
  }

  function formatarCep(valor) {
    var d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(valor) {
    var d = digitos(valor).slice(0, 8);
    var saida = d.slice(0, 2);
    if (d.length > 2) saida += "/" + d.slice(2, 4);
    if (d.length > 4) saida += "/" + d.slice(4, 8);
    return saida;
  }

  function formatarCampos(form) {
    Object.keys(FORMATADORES).forEach(function (nome) {
      var campo = form.elements[nome];
      if (campo) campo.value = FORMATADORES[nome](campo.value);
    });
  }

  function mostrarErros(form, mensagens) {
    var caixa = form.querySelector(".erros");
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      var p = document.createElement("p");
      p.textContent = mensagem;
      caixa.appendChild(p);
    });
    caixa.hidden = mensagens.length === 0;
  }

  function mostrarConfirmacao(oficio) {
    document.getElementById("app").hidden = true;
    document.getElementById("oficio").textContent = oficio;
    document.getElementById("confirmacao").hidden = false;
    window.scrollTo(0, 0);
  }

  async function enviar(evento) {
    evento.preventDefault();
    var form = evento.target;
    formatarCampos(form);
    var dados = { aba: form.dataset.aba };
    form.querySelectorAll("[name]").forEach(function (campo) {
      dados[campo.name] = campo.value.trim();
    });
    var resultado;
    try {
      var resposta = await fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      });
      resultado = await resposta.json();
    } catch (erro) {
      mostrarErros(form, ["Não foi possível enviar a solicitação."]);
      return;
    }
    if (resultado.ok) {
      mostrarConfirmacao(resultado.oficio);
    } else {
      mostrarErros(form, resultado.erros || ["Não foi possível enviar a solicitação."]);
      window.scrollTo(0, 0);
    }
  }

  function configurarAbas() {
    var abas = document.querySelectorAll(".aba");
    var paineis = document.querySelectorAll(".painel");
    abas.forEach(function (aba) {
      aba.addEventListener("click", function () {
        abas.forEach(function (outra) {
          var ativa = outra === aba;
          outra.classList.toggle("ativa", ativa);
          outra.setAttribute("aria-selected", ativa ? "true" : "false");
        });
        paineis.forEach(function (painel) {
          painel.hidden = painel.dataset.aba !== aba.dataset.aba;
        });
      });
    });
  }

  function configurarFormularios() {
    document.querySelectorAll(".painel").forEach(function (form) {
      form.addEventListener("focusout", function (evento) {
        var formatar = FORMATADORES[evento.target.name];
        if (formatar) evento.target.value = formatar(evento.target.value);
      });
      form.addEventListener("submit", enviar);
    });
  }

  configurarAbas();
  configurarFormularios();
})();
