(function () {
  "use strict";

  function apenasDigitos(texto) {
    return (texto || "").replace(/\D/g, "");
  }

  function formatarCPF(valor) {
    var d = apenasDigitos(valor).slice(0, 11);
    var formatado = d.slice(0, 3);
    if (d.length > 3) { formatado += "." + d.slice(3, 6); }
    if (d.length > 6) { formatado += "." + d.slice(6, 9); }
    if (d.length > 9) { formatado += "-" + d.slice(9, 11); }
    return formatado;
  }

  function formatarCEP(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length <= 5) { return d; }
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formatarData(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length <= 2) { return d; }
    if (d.length <= 4) { return d.slice(0, 2) + "/" + d.slice(2); }
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  function formatarValor(valor) {
    var d = apenasDigitos(valor);
    if (d === "") { return ""; }
    var centavos = parseInt(d, 10);
    var reais = Math.floor(centavos / 100);
    var resto = centavos % 100;
    var milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + milhar + "," + ("0" + resto).slice(-2);
  }

  var FORMATOS = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data: formatarData
  };

  function aplicarFormato(campo) {
    var formatar = FORMATOS[campo.getAttribute("data-formato")];
    if (formatar) { campo.value = formatar(campo.value); }
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-formato]"), function (campo) {
    campo.addEventListener("blur", function () { aplicarFormato(campo); });
  });

  var abas = [
    { botao: document.getElementById("aba-alunos"), painel: document.getElementById("painel-alunos") },
    { botao: document.getElementById("aba-docentes"), painel: document.getElementById("painel-docentes") }
  ];

  function ativarAba(indice) {
    abas.forEach(function (aba, i) {
      var ativa = i === indice;
      aba.botao.classList.toggle("ativa", ativa);
      aba.botao.setAttribute("aria-selected", ativa ? "true" : "false");
      aba.painel.hidden = !ativa;
    });
  }

  abas.forEach(function (aba, i) {
    aba.botao.addEventListener("click", function () { ativarAba(i); });
  });

  function lerDados(form) {
    Array.prototype.forEach.call(form.querySelectorAll("[data-formato]"), aplicarFormato);
    var dados = {};
    Array.prototype.forEach.call(form.elements, function (campo) {
      if (campo.name) { dados[campo.name] = campo.value.trim(); }
    });
    dados.valor_solicitado = apenasDigitos(dados.valor_solicitado);
    return dados;
  }

  function mostrarErros(form, mensagens) {
    var caixa = form.querySelector(".mensagens");
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = mensagens.length === 0;
  }

  function enviar(form) {
    var dados = lerDados(form);
    fetch(form.getAttribute("data-endpoint"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) { return resposta.json(); })
      .then(function (corpo) {
        if (corpo.oficio) {
          document.getElementById("oficio").textContent = corpo.oficio;
          document.getElementById("pagina-formulario").hidden = true;
          document.getElementById("pagina-confirmacao").hidden = false;
        } else {
          mostrarErros(form, corpo.erros || []);
        }
      });
  }

  Array.prototype.forEach.call(document.querySelectorAll("form.formulario"), function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form);
    });
  });
})();
