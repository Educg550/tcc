"use strict";

function formatarMoeda(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 15);
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  const inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const resto = String(centavos % 100).padStart(2, "0");
  return "R$ " + inteiro + "," + resto;
}

function formatarCPF(valor) {
  let digitos = valor.replace(/\D/g, "").slice(0, 11);
  digitos = digitos.replace(/(\d{3})(\d)/, "$1.$2");
  digitos = digitos.replace(/(\d{3})\.(\d{3})(\d)/, "$1.$2.$3");
  return digitos.replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
}

function formatarCEP(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 8);
  if (digitos.length <= 2) {
    return digitos;
  }
  if (digitos.length <= 4) {
    return digitos.slice(0, 2) + "/" + digitos.slice(2);
  }
  return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
}

const FORMATOS = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

document.querySelectorAll("input[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = FORMATOS[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".painel").forEach(function (painel) {
      painel.hidden = painel.id !== "painel-" + aba.dataset.aba;
    });
  });
});

function mostrarErros(container, mensagens) {
  container.textContent = "";
  mensagens.forEach(function (mensagem) {
    const linha = document.createElement("div");
    linha.textContent = mensagem;
    container.appendChild(linha);
  });
  container.hidden = false;
}

document.querySelectorAll(".formulario").forEach(function (formulario) {
  formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();
    const dados = { aba: formulario.dataset.aba };
    formulario.querySelectorAll("[data-rotulo]").forEach(function (campo) {
      dados[campo.dataset.rotulo] = campo.value;
    });

    fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then(function (resposta) {
        return resposta.json();
      })
      .then(function (resultado) {
        const erros = formulario.parentElement.querySelector(".erros");
        if (resultado.erros) {
          mostrarErros(erros, resultado.erros);
          return;
        }
        erros.hidden = true;
        document.querySelectorAll(".painel").forEach(function (painel) {
          painel.hidden = true;
        });
        document.querySelector(".abas").hidden = true;
        document.getElementById("oficio").textContent = resultado.oficio;
        document.getElementById("confirmacao").hidden = false;
      });
  });
});
