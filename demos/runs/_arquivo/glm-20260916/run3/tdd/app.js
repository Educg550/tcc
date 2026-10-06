"use strict";

function digitos(texto) {
  return String(texto).replace(/\D/g, "");
}

function formatarValor(texto) {
  const d = digitos(texto);
  if (!d) {
    return "";
  }
  const centavos = d.slice(-2).padStart(2, "0");
  const inteiro = d.slice(0, -2) || "0";
  const milhar = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + milhar + "," + centavos;
}

function formatarCpf(texto) {
  const d = digitos(texto).slice(0, 11);
  if (d.length <= 3) {
    return d;
  }
  if (d.length <= 6) {
    return d.slice(0, 3) + "." + d.slice(3);
  }
  if (d.length <= 9) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  }
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(texto) {
  const d = digitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length <= 2) {
    return d;
  }
  if (d.length <= 4) {
    return d.slice(0, 2) + "/" + d.slice(2);
  }
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

document.querySelectorAll("[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    const formatar = FORMATADORES[campo.dataset.formato];
    if (formatar) {
      campo.value = formatar(campo.value);
    }
  });
});

const abas = document.querySelectorAll(".aba");
const paineis = document.querySelectorAll(".painel-formulario");

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    paineis.forEach(function (painel) {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll(".formulario").forEach(function (formulario) {
  formulario.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(formulario).entries());
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.();
    const caixaDeErros = formulario.querySelector(".erros");
    if (corpo.erros && corpo.erros.length > 0) {
      caixaDeErros.replaceChildren();
      corpo.erros.forEach(function (mensagem) {
        const paragrafo = document.createElement("p");
        paragrafo.textContent = mensagem;
        caixaDeErros.appendChild(paragrafo);
      });
      caixaDeErros.hidden = false;
      return;
    }
    caixaDeErros.hidden = true;
    document.getElementById("texto-do-oficio").textContent = corpo.oficio;
    document.getElementById("confirmacao").hidden = false;
    paineis.forEach(function (painel) {
      painel.hidden = true;
    });
    document.querySelector(".abas").hidden = true;
  });
});
