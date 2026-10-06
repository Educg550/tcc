/* Comportamento de tela do formulário de auxílio financeiro. */

(function () {
  "use strict";

  var tabAlunos = document.getElementById("tab-alunos");
  var tabDocentes = document.getElementById("tab-docentes");
  var formAlunos = document.getElementById("form-alunos");
  var formDocentes = document.getElementById("form-docentes");
  var confirmacao = document.getElementById("confirmacao");
  var barraDeAbas = document.querySelector(".abas");

  function mostrarAba(alunos) {
    formAlunos.hidden = !alunos;
    formDocentes.hidden = alunos;
    tabAlunos.classList.toggle("active", alunos);
    tabDocentes.classList.toggle("active", !alunos);
  }

  tabAlunos.addEventListener("click", function () {
    mostrarAba(true);
  });

  tabDocentes.addEventListener("click", function () {
    mostrarAba(false);
  });

  function apenasDigitos(valor) {
    return (valor || "").replace(/\D+/g, "");
  }

  function formatarValor(valor) {
    var digitos = apenasDigitos(valor);
    if (!digitos) {
      return "";
    }
    var reais = digitos.slice(0, -2) || "0";
    var centavos = digitos.slice(-2);
    if (centavos.length < 2) {
      centavos = "0" + centavos;
    }
    reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formatarCpf(valor) {
    var d = apenasDigitos(valor);
    var texto = d.slice(0, 3);
    if (d.length > 3) {
      texto += "." + d.slice(3, 6);
    }
    if (d.length > 6) {
      texto += "." + d.slice(6, 9);
    }
    if (d.length > 9) {
      texto += "-" + d.slice(9, 11);
    }
    return texto;
  }

  function formatarCep(valor) {
    var d = apenasDigitos(valor);
    if (d.length <= 5) {
      return d;
    }
    return d.slice(0, 5) + "-" + d.slice(5, 8);
  }

  function formatarData(valor) {
    var d = apenasDigitos(valor);
    if (d.length <= 2) {
      return d;
    }
    if (d.length <= 4) {
      return d.slice(0, 2) + "/" + d.slice(2, 4);
    }
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4, 8);
  }

  function aoSair(prefixo, sufixo, formatador) {
    var campo = document.getElementById(prefixo + sufixo);
    campo.addEventListener("blur", function () {
      campo.value = formatador(campo.value);
    });
  }

  ["alunos", "docentes"].forEach(function (prefixo) {
    aoSair(prefixo, "-valor", formatarValor);
    aoSair(prefixo, "-cpf", formatarCpf);
    aoSair(prefixo, "-cep", formatarCep);
    aoSair(prefixo, "-nascimento", formatarData);
  });

  function coletarDados(form, tipo) {
    var dados = { tipo: tipo };
    var campos = form.querySelectorAll("input[name], select[name], textarea[name]");
    var indice;
    for (indice = 0; indice < campos.length; indice++) {
      dados[campos[indice].name] = campos[indice].value;
    }
    var centavos = apenasDigitos(dados.valor);
    dados.valor = centavos ? parseInt(centavos, 10) : "";
    return dados;
  }

  function mostrarErros(caixa, erros) {
    caixa.innerHTML = "";
    erros.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function mostrarConfirmacao(titulo, oficio) {
    barraDeAbas.hidden = true;
    formAlunos.hidden = true;
    formDocentes.hidden = true;
    document.getElementById("titulo-confirmacao").textContent = titulo;
    document.getElementById("texto-oficio").textContent = oficio;
    confirmacao.hidden = false;
  }

  function ligarEnvio(form, tipo, idCaixaErros) {
    var caixa = document.getElementById(idCaixaErros);
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(coletarDados(form, tipo))
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (corpo) {
          if (corpo.ok) {
            mostrarConfirmacao(corpo.titulo, corpo.oficio);
          } else {
            mostrarErros(caixa, corpo.erros);
          }
        });
    });
  }

  ligarEnvio(formAlunos, "alunos", "erros-alunos");
  ligarEnvio(formDocentes, "docentes", "erros-docentes");
})();
