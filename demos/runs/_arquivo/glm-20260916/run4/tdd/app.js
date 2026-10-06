"use strict";

function digitos(valor) {
  return valor.replace(/\D/g, "");
}

function emReais(digitosValor) {
  const centavos = parseInt(digitosValor, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function formatarMoeda(campo) {
  const d = digitos(campo.value);
  campo.value = d ? emReais(d) : "";
}

function formatarCpf(campo) {
  campo.value = digitos(campo.value)
    .slice(0, 11)
    .replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, "$1.$2.$3-$4");
}

function formatarCep(campo) {
  campo.value = digitos(campo.value)
    .slice(0, 8)
    .replace(/^(\d{5})(\d{1,3})$/, "$1-$2");
}

function formatarData(campo) {
  const d = digitos(campo.value).slice(0, 8);
  if (d.length <= 2) {
    campo.value = d;
  } else if (d.length <= 4) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2);
  } else {
    campo.value = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }
}

[
  [".fmt-moeda", formatarMoeda],
  [".fmt-cpf", formatarCpf],
  [".fmt-cep", formatarCep],
  [".fmt-data", formatarData],
].forEach(function (par) {
  document.querySelectorAll(par[0]).forEach(function (campo) {
    campo.addEventListener("blur", function () {
      par[1](campo);
    });
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

async function enviar(formulario) {
  const dados = { ABA: formulario.dataset.aba };
  new FormData(formulario).forEach(function (valor, campo) {
    dados[campo] = valor;
  });
  dados["VALOR SOLICITADO (R$)"] = digitos(dados["VALOR SOLICITADO (R$)"] || "");

  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/" },
    body: JSON.stringify(dados),
  });
  const resultado = await resposta.();
  const caixa = formulario.querySelector(".erros");

  if (resultado.erros && resultado.erros.length > 0) {
    caixa.textContent = resultado.erros.join("\n");
    return;
  }

  caixa.textContent = "";
  document.getElementById("formulario").hidden = true;
  document.getElementById("confirmacao").hidden = false;
  document.getElementById("oficio").textContent = resultado.oficio;
  window.scrollTo(0, 0);
}

document.querySelectorAll(".solicitacao").forEach(function (formulario) {
  formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();
    enviar(formulario);
  });
});
