(function () {
  "use strict";

  function digitos(valor) {
    return String(valor || "").replace(/\D/g, "");
  }

  function milhar(numero) {
    var texto = String(numero);
    var saida = "";
    while (texto.length > 3) {
      saida = "." + texto.slice(-3) + saida;
      texto = texto.slice(0, -3);
    }
    return texto + saida;
  }

  function mascaraValor(valor) {
    var d = digitos(valor);
    if (!d) {
      return "";
    }
    var total = parseInt(d, 10);
    var centavos = "0" + String(total % 100);
    return "R$ " + milhar(Math.floor(total / 100)) + "," + centavos.slice(-2);
  }

  function mascaraCPF(valor) {
    var d = digitos(valor);
    if (!d) {
      return "";
    }
    var saida = d.slice(0, 3);
    if (d.length > 3) {
      saida += "." + d.slice(3, 6);
    }
    if (d.length > 6) {
      saida += "." + d.slice(6, 9);
    }
    if (d.length > 9) {
      saida += "-" + d.slice(9, 11);
    }
    return saida;
  }

  function mascaraCEP(valor) {
    var d = digitos(valor);
    if (!d) {
      return "";
    }
    if (d.length > 5) {
      return d.slice(0, 5) + "-" + d.slice(5, 8);
    }
    return d;
  }

  function mascaraData(valor) {
    var d = digitos(valor);
    if (!d) {
      return "";
    }
    var saida = d.slice(0, 2);
    if (d.length > 2) {
      saida += "/" + d.slice(2, 4);
    }
    if (d.length > 4) {
      saida += "/" + d.slice(4, 8);
    }
    return saida;
  }

  var formularios = Array.prototype.slice.call(document.querySelectorAll("form"));

  formularios.forEach(function (formulario) {
    var mascaras = [
      ["#valor_solicitado", mascaraValor],
      ["#cpf", mascaraCPF],
      ["#cep", mascaraCEP],
      ["#data_de_nascimento", mascaraData]
    ];
    mascaras.forEach(function (par) {
      var campo = formulario.querySelector(par[0]);
      if (!campo) {
        return;
      }
      campo.addEventListener("input", function () {
        campo.value = par[1](campo.value);
      });
      campo.addEventListener("blur", function () {
        campo.value = par[1](campo.value);
      });
    });
  });

  function mostrarAba(nome) {
    ["alunos", "docentes"].forEach(function (aba) {
      document.getElementById("tab-" + aba).classList.toggle("ativa", aba === nome);
      document.getElementById("form-" + aba).classList.toggle("oculto", aba !== nome);
    });
  }

  document.getElementById("tab-alunos").addEventListener("click", function () {
    mostrarAba("alunos");
  });

  document.getElementById("tab-docentes").addEventListener("click", function () {
    mostrarAba("docentes");
  });

  formularios.forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = { aba: formulario.getAttribute("data-aba") };
      new FormData(formulario).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json().then(function (corpo) {
            return { ok: resposta.ok, corpo: corpo };
          });
        })
        .then(function (resultado) {
          var mensagens = formulario.querySelector(".mensagens");
          mensagens.innerHTML = "";
          if (resultado.ok) {
            document.querySelector("main").classList.add("oculto");
            document.getElementById("oficio").textContent = resultado.corpo.oficio;
            document.getElementById("confirmacao").classList.remove("oculto");
            return;
          }
          resultado.corpo.erros.forEach(function (erro) {
            var linha = document.createElement("p");
            linha.textContent = erro;
            mensagens.appendChild(linha);
          });
          mensagens.classList.remove("oculto");
        });
    });
  });
})();
