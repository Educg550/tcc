(function () {
  "use strict";

  function selecionarAba(nome) {
    document.querySelectorAll(".aba").forEach(function (botao) {
      botao.classList.toggle("ativa", botao.dataset.aba === nome);
    });
    document.querySelectorAll(".formulario").forEach(function (formulario) {
      formulario.classList.toggle("ativa", formulario.dataset.aba === nome);
    });
  }

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      selecionarAba(botao.dataset.aba);
    });
  });

  function digitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formatarMoeda(campo) {
    var d = digitos(campo.value);
    if (!d) {
      campo.value = "";
      return;
    }
    campo.value = "R$ " + (parseInt(d, 10) / 100).toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function formatarCpf(campo) {
    var d = digitos(campo.value).slice(0, 11);
    if (d.length > 9) {
      campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    } else if (d.length > 6) {
      campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    } else if (d.length > 3) {
      campo.value = d.slice(0, 3) + "." + d.slice(3);
    } else {
      campo.value = d;
    }
  }

  function formatarCep(campo) {
    var d = digitos(campo.value).slice(0, 8);
    campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(campo) {
    var d = digitos(campo.value).slice(0, 8);
    var partes;
    if (d.length > 4) {
      partes = [d.slice(0, 2), d.slice(2, 4), d.slice(4)];
    } else if (d.length > 2) {
      partes = [d.slice(0, 2), d.slice(2)];
    } else {
      partes = [d];
    }
    campo.value = partes.join("/");
  }

  var formatadores = {
    valor_solicitado: formatarMoeda,
    cpf: formatarCpf,
    cep: formatarCep,
    data_nascimento: formatarData
  };

  Object.keys(formatadores).forEach(function (nome) {
    document.querySelectorAll('[name="' + nome + '"]').forEach(function (campo) {
      campo.addEventListener("blur", function () {
        formatadores[nome](campo);
      });
    });
  });

  function escapar(texto) {
    var div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  if (window.__resposta) {
    var resposta = window.__resposta;
    selecionarAba(resposta.aba);
    var formulario = document.querySelector('.formulario[data-aba="' + resposta.aba + '"]');
    formulario.querySelector(".erros").innerHTML = resposta.erros.map(function (erro) {
      return "<div>" + escapar(erro) + "</div>";
    }).join("");
    Object.keys(resposta.valores).forEach(function (nome) {
      var campo = formulario.elements[nome];
      if (campo) {
        campo.value = resposta.valores[nome];
      }
    });
  }
})();
