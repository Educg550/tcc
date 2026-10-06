"use strict";

function apenasDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarMoeda(valor) {
  const digitos = apenasDigitos(valor);
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  let reais = String(Math.floor(centavos / 100));
  let comMilhar = "";
  while (reais.length > 3) {
    comMilhar = "." + reais.slice(-3) + comMilhar;
    reais = reais.slice(0, -3);
  }
  return "R$ " + reais + comMilhar + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCpf(valor) {
  const d = apenasDigitos(valor).slice(0, 11);
  let formatado = d.slice(0, 3);
  if (d.length > 3) formatado += "." + d.slice(3, 6);
  if (d.length > 6) formatado += "." + d.slice(6, 9);
  if (d.length > 9) formatado += "-" + d.slice(9);
  return formatado;
}

function formatarCep(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  let formatado = d.slice(0, 2);
  if (d.length > 2) formatado += "/" + d.slice(2, 4);
  if (d.length > 4) formatado += "/" + d.slice(4);
  return formatado;
}

const FORMATADORES = {
  valor: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

document.querySelectorAll("input[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
      outra.setAttribute("aria-selected", outra === aba ? "true" : "false");
    });
    document.querySelectorAll(".formulario").forEach(function (formulario) {
      formulario.hidden = formulario.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll(".formulario").forEach(function (formulario) {
  formulario.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const dados = { perfil: formulario.dataset.perfil };
    formulario.querySelectorAll("[name]").forEach(function (campo) {
      dados[campo.name] = campo.value;
    });
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.();
    if (resultado.erros.length > 0) {
      const caixa = formulario.querySelector(".erros");
      caixa.textContent = resultado.erros.join("\n");
      caixa.hidden = false;
      return;
    }
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("visao-formulario").hidden = true;
    document.getElementById("visao-confirmacao").hidden = false;
  });
});
