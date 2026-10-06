document.addEventListener("DOMContentLoaded", function () {
  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");
  var confirmacao = document.getElementById("confirmacao");
  var oficio = document.getElementById("oficio");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      formularios.forEach(function (formulario) {
        formulario.classList.toggle("ativo", formulario.dataset.aba === aba.dataset.aba);
      });
    });
  });

  function soDigitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formataValor(input) {
    var digitos = soDigitos(input.value).replace(/^0+(?=\d)/, "");
    if (!digitos) {
      input.value = "";
      return;
    }
    var numero = digitos.padStart(3, "0");
    var centavos = numero.slice(-2);
    var inteiro = numero.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    input.value = "R$ " + inteiro + "," + centavos;
  }

  function formataCPF(input) {
    var digitos = soDigitos(input.value).slice(0, 11);
    if (digitos.length === 11) {
      input.value = digitos.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
    }
  }

  function formataCEP(input) {
    var digitos = soDigitos(input.value).slice(0, 8);
    if (digitos.length === 8) {
      input.value = digitos.replace(/^(\d{5})(\d{3})$/, "$1-$2");
    }
  }

  function formataData(input) {
    var digitos = soDigitos(input.value).slice(0, 8);
    if (digitos.length === 8) {
      input.value = digitos.replace(/^(\d{2})(\d{2})(\d{4})$/, "$1/$2/$3");
    }
  }

  var formatadores = {
    valor_solicitado: formataValor,
    cpf: formataCPF,
    cep: formataCEP,
    data_nascimento: formataData
  };

  document.querySelectorAll("input").forEach(function (input) {
    var formatador = formatadores[input.name];
    if (formatador) {
      input.addEventListener("blur", function () {
        formatador(input);
      });
    }
  });

  formularios.forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(formulario).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      dados.aba = formulario.dataset.aba;
      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resposta) {
          var erros = formulario.querySelector(".erros");
          if (resposta.ok) {
            formularios.forEach(function (outro) {
              outro.classList.remove("ativo");
            });
            document.querySelector(".abas").hidden = true;
            oficio.textContent = resposta.oficio;
            confirmacao.hidden = false;
            window.scrollTo(0, 0);
          } else {
            erros.textContent = "";
            resposta.erros.forEach(function (mensagem) {
              var linha = document.createElement("div");
              linha.textContent = mensagem;
              erros.appendChild(linha);
            });
            erros.hidden = false;
          }
        });
    });
  });
});
