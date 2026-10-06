(function () {
  "use strict";

  var abas = Array.prototype.slice.call(document.querySelectorAll(".aba"));
  var paineis = {
    alunos: document.getElementById("form-alunos"),
    docentes: document.getElementById("form-docentes"),
  };

  function selecionarAba(nome) {
    abas.forEach(function (aba) {
      aba.classList.toggle("ativa", aba.dataset.aba === nome);
    });
    Object.keys(paineis).forEach(function (chave) {
      paineis[chave].classList.toggle("oculto", chave !== nome);
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      selecionarAba(aba.dataset.aba);
    });
  });

  function apenasDigitos(valor) {
    return String(valor || "").replace(/\D/g, "");
  }

  function formatarMoeda(valor) {
    var digitos = apenasDigitos(valor);
    if (!digitos) return "";
    var numero = parseInt(digitos, 10);
    var reais = String(Math.floor(numero / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    var centavos = String(numero % 100).padStart(2, "0");
    return "R$ " + reais + "," + centavos;
  }

  function formatarCPF(valor) {
    var d = apenasDigitos(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  function formatarCEP(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formatarData(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var formatadores = {
    valor_solicitado: formatarMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData,
  };

  var formularios = Array.prototype.slice.call(document.querySelectorAll("form"));

  formularios.forEach(function (form) {
    Object.keys(formatadores).forEach(function (nome) {
      var campo = form.elements.namedItem(nome);
      if (campo) {
        campo.addEventListener("blur", function () {
          campo.value = formatadores[nome](campo.value);
        });
      }
    });

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form);
    });
  });

  function enviar(form) {
    var caixaErros = form.querySelector(".erros");
    var dados = {};
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    dados.aba = form.dataset.aba;

    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then(function (resposta) {
        return resposta.json();
      })
      .then(function (corpo) {
        if (corpo.erros && corpo.erros.length) {
          caixaErros.innerHTML = "";
          corpo.erros.forEach(function (mensagem) {
            var linha = document.createElement("p");
            linha.textContent = mensagem;
            caixaErros.appendChild(linha);
          });
          caixaErros.hidden = false;
          return;
        }
        caixaErros.hidden = true;
        document.getElementById("oficio").textContent = corpo.oficio;
        document.getElementById("formularios").classList.add("oculto");
        document.getElementById("confirmacao").classList.remove("oculto");
      });
  }
})();
