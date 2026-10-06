(function () {
  "use strict";

  function soDigitos(valor) {
    return valor.replace(/[^0-9]/g, "");
  }

  function separaMilhares(digitos) {
    var saida = "";
    var contador = 0;
    for (var i = digitos.length - 1; i >= 0; i--) {
      saida = digitos[i] + saida;
      contador++;
      if (contador % 3 === 0 && i > 0) {
        saida = "." + saida;
      }
    }
    return saida;
  }

  function mascaraValor(valor) {
    var digitos = soDigitos(valor);
    if (!digitos) {
      return "";
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = centavos % 100;
    return "R$ " + separaMilhares(String(reais)) + "," + String(resto).padStart(2, "0");
  }

  function mascaraCpf(valor) {
    var d = soDigitos(valor).slice(0, 11);
    if (d.length > 9) {
      return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    }
    if (d.length > 6) {
      return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    }
    if (d.length > 3) {
      return d.slice(0, 3) + "." + d.slice(3);
    }
    return d;
  }

  function mascaraCep(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 5) {
      return d.slice(0, 5) + "-" + d.slice(5);
    }
    return d;
  }

  function mascaraData(valor) {
    var d = soDigitos(valor).slice(0, 8);
    if (d.length > 4) {
      return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    }
    if (d.length > 2) {
      return d.slice(0, 2) + "/" + d.slice(2);
    }
    return d;
  }

  var MASCARAS = {
    valor: mascaraValor,
    cpf: mascaraCpf,
    cep: mascaraCep,
    nascimento: mascaraData
  };

  Array.prototype.forEach.call(document.querySelectorAll("input"), function (campo) {
    var mascara = MASCARAS[campo.name];
    if (!mascara) {
      return;
    }
    campo.addEventListener("blur", function () {
      campo.value = mascara(campo.value);
    });
  });

  var abas = Array.prototype.slice.call(document.querySelectorAll(".aba"));
  var painelAlunos = document.getElementById("painel-alunos");
  var painelDocentes = document.getElementById("painel-docentes");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        var ativa = outra === aba;
        outra.classList.toggle("ativa", ativa);
        outra.setAttribute("aria-selected", ativa ? "true" : "false");
      });
      painelAlunos.classList.toggle("oculto", aba.dataset.aba !== "alunos");
      painelDocentes.classList.toggle("oculto", aba.dataset.aba !== "docentes");
    });
  });

  function mostrarConfirmacao(oficio) {
    document.getElementById("oficio").textContent = oficio;
    painelAlunos.classList.add("oculto");
    painelDocentes.classList.add("oculto");
    document.querySelector(".abas").classList.add("oculto");
    document.getElementById("painel-confirmacao").classList.remove("oculto");
  }

  Array.prototype.forEach.call(document.querySelectorAll(".formulario"), function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var caixa = form.querySelector(".erros");

      Array.prototype.forEach.call(form.querySelectorAll("input, textarea"), function (campo) {
        var mascara = MASCARAS[campo.name];
        if (mascara) {
          campo.value = mascara(campo.value);
        }
      });

      var dados = { aba: form.dataset.aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          if (resultado.erros && resultado.erros.length) {
            caixa.textContent = resultado.erros.join("\n");
            caixa.classList.add("visivel");
          } else {
            caixa.textContent = "";
            caixa.classList.remove("visivel");
            mostrarConfirmacao(resultado.oficio);
          }
        });
    });
  });
})();
