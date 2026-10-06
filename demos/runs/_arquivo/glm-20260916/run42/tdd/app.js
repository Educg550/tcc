"use strict";

var FORMATADORES = {
  "VALOR SOLICITADO (R$)": formatarMoeda,
  "DATA DE NASCIMENTO": formatarData,
  "CEP": formatarCep,
  "CPF (SEPARADOS POR PONTOS E TRAÇO)": formatarCpf
};

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function agruparMilhares(parteInteira) {
  return parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function formatarMoeda(campo) {
  var d = digitos(campo.value);
  if (!d) {
    campo.value = "";
    return;
  }
  var reais = d.slice(0, -2) || "0";
  var centavos = d.slice(-2).padStart(2, "0");
  campo.value = "R$ " + agruparMilhares(reais) + "," + centavos;
}

function formatarData(campo) {
  var d = digitos(campo.value).slice(0, 8);
  var texto = d.slice(0, 2);
  if (d.length > 2) {
    texto += "/" + d.slice(2, 4);
  }
  if (d.length > 4) {
    texto += "/" + d.slice(4, 8);
  }
  campo.value = texto;
}

function formatarCep(campo) {
  var d = digitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
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

document.querySelectorAll("input[name]").forEach(function (campo) {
  var formatar = FORMATADORES[campo.name];
  if (formatar) {
    campo.addEventListener("blur", function () {
      formatar(campo);
    });
  }
});

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".painel").forEach(function (painel) {
      painel.classList.toggle("oculto", painel.id !== aba.dataset.alvo);
    });
  });
});

function coletar(form) {
  var dados = {};
  form.querySelectorAll("[name]").forEach(function (campo) {
    dados[campo.name] = campo.value.trim();
  });
  return dados;
}

function mostrarErros(form, mensagens) {
  var area = form.querySelector(".erros");
  area.textContent = "";
  mensagens.forEach(function (mensagem) {
    var paragrafo = document.createElement("p");
    paragrafo.textContent = mensagem;
    area.appendChild(paragrafo);
  });
}

function mostrarOficio(oficio) {
  document.getElementById("oficio").textContent = oficio;
  document.querySelector(".abas").classList.add("oculto");
  document.querySelectorAll(".painel").forEach(function (painel) {
    painel.classList.add("oculto");
  });
  document.getElementById("confirmacao").classList.remove("oculto");
}

document.querySelectorAll("form.painel").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(coletar(form))
    })
      .then(function (resposta) {
        return resposta.();
      })
      .then(function (dados) {
        if (dados.ok) {
          mostrarOficio(dados.oficio);
        } else {
          mostrarErros(form, dados.erros);
        }
      });
  });
});
