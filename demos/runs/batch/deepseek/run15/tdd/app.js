(function () {
  "use strict";

  function formataValor(texto) {
    var digitos = texto.replace(/\D/g, "");
    if (!digitos) {
      return "";
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100).toLocaleString("pt-BR");
    var resto = String(centavos % 100).padStart(2, "0");
    return "R$ " + reais + "," + resto;
  }

  function formataCpf(texto) {
    var d = texto.replace(/\D/g, "").slice(0, 11);
    if (d.length !== 11) {
      return texto;
    }
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function formataCep(texto) {
    var d = texto.replace(/\D/g, "").slice(0, 8);
    if (d.length !== 8) {
      return texto;
    }
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formataData(texto) {
    var d = texto.replace(/\D/g, "").slice(0, 8);
    if (d.length !== 8) {
      return texto;
    }
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  var FORMATADORES = {
    valor_solicitado: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data_nascimento: formataData
  };

  Object.keys(FORMATADORES).forEach(function (nome) {
    document.querySelectorAll('[name="' + nome + '"]').forEach(function (campo) {
      campo.addEventListener("blur", function () {
        campo.value = FORMATADORES[nome](campo.value);
      });
    });
  });

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (outro) {
        outro.classList.remove("ativa");
      });
      botao.classList.add("ativa");
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.classList.remove("ativa");
      });
      document.getElementById("painel-" + botao.dataset.aba).classList.add("ativa");
    });
  });

  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      fetch("/api/" + form.dataset.aba, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          var caixa = document.getElementById("erros-" + form.dataset.aba);
          caixa.textContent = "";
          if (resultado.erros && resultado.erros.length) {
            resultado.erros.forEach(function (mensagem) {
              var linha = document.createElement("div");
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            return;
          }
          document.getElementById("oficio").textContent = resultado.oficio;
          document.querySelector(".abas").classList.add("escondido");
          document.querySelectorAll(".painel").forEach(function (painel) {
            painel.classList.remove("ativa");
          });
          document.getElementById("confirmacao").classList.remove("escondido");
        });
    });
  });
})();
