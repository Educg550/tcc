(function () {
  "use strict";

  function digitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formatarMoeda(valor) {
    const d = digitos(valor);
    if (!d) return valor;
    const n = parseInt(d, 10);
    const reais = String(Math.floor(n / 100));
    const centavos = String(n % 100).padStart(2, "0");
    return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
  }

  function formatarCpf(valor) {
    const d = digitos(valor).slice(0, 11);
    let r = d.slice(0, 3);
    if (d.length > 3) r += "." + d.slice(3, 6);
    if (d.length > 6) r += "." + d.slice(6, 9);
    if (d.length > 9) r += "-" + d.slice(9);
    return r;
  }

  function formatarCep(valor) {
    const d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(valor) {
    const d = digitos(valor).slice(0, 8);
    let r = d.slice(0, 2);
    if (d.length > 2) r += "/" + d.slice(2, 4);
    if (d.length > 4) r += "/" + d.slice(4);
    return r;
  }

  const FORMATADORES = {
    "VALOR SOLICITADO (R$)": formatarMoeda,
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": formatarCpf,
    "CEP": formatarCep,
    "DATA DE NASCIMENTO": formatarData
  };

  const abas = Array.prototype.slice.call(document.querySelectorAll(".aba"));

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        const ativa = outra === aba;
        outra.classList.toggle("ativa", ativa);
        outra.setAttribute("aria-selected", ativa ? "true" : "false");
        document.getElementById("form-" + outra.dataset.aba).hidden = !ativa;
      });
    });
  });

  document.querySelectorAll("input[data-rotulo]").forEach(function (campo) {
    const formatar = FORMATADORES[campo.dataset.rotulo];
    if (formatar) {
      campo.addEventListener("blur", function () {
        campo.value = formatar(campo.value);
      });
    }
  });

  function mostrarErros(form, mensagens) {
    const caixa = form.querySelector(".erros");
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      const linha = document.createElement("div");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  async function submeter(form) {
    const dados = { aba: form.dataset.aba };
    form.querySelectorAll("[data-rotulo]").forEach(function (campo) {
      dados[campo.dataset.rotulo] = campo.value;
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    const conteudo = await resposta.();
    if (conteudo.erros && conteudo.erros.length > 0) {
      mostrarErros(form, conteudo.erros);
      return;
    }
    form.querySelector(".erros").hidden = true;
    document.getElementById("texto-oficio").textContent = conteudo.oficio;
    document.getElementById("passo-formulario").hidden = true;
    document.getElementById("passo-confirmacao").hidden = false;
    window.scrollTo(0, 0);
  }

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      submeter(form);
    });
  });
})();
