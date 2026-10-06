"use strict";

function apenasDigitos(texto) {
  return texto.replace(/[^0-9]/g, "");
}

function aplicarPadrao(texto, padrao) {
  const digitos = apenasDigitos(texto);
  let saida = "";
  let i = 0;
  for (const caractere of padrao) {
    if (i >= digitos.length) break;
    saida += caractere === "#" ? digitos[i++] : caractere;
  }
  return saida;
}

function formatarValor(texto) {
  const digitos = apenasDigitos(texto);
  if (!digitos) return "";
  const reais = Number(digitos) / 100;
  return "R$ " + reais.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const MASCARAS = {
  valor: formatarValor,
  cpf: (texto) => aplicarPadrao(texto, "###.###.###-##"),
  cep: (texto) => aplicarPadrao(texto, "#####-###"),
  data: (texto) => aplicarPadrao(texto, "##/##/####"),
};

document.querySelectorAll("[data-mascara]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = MASCARAS[campo.dataset.mascara](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
const paineis = document.querySelectorAll(".painel");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", String(ativa));
    });
    paineis.forEach((painel) => {
      painel.classList.toggle("ativo", painel.dataset.painel === aba.dataset.aba);
    });
  });
});

function mostrarConfirmacao(oficio) {
  document.body.classList.add("confirmado");
  document.getElementById("confirmacao").hidden = false;
  document.querySelector(".oficio").textContent = oficio;
}

document.querySelectorAll("form").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(formulario).entries());
    dados.aba = formulario.dataset.aba;
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    const erros = formulario.querySelector(".erros");
    if (resultado.erros.length > 0) {
      erros.textContent = resultado.erros.join("\n");
      erros.hidden = false;
      return;
    }
    erros.hidden = true;
    mostrarConfirmacao(resultado.oficio);
  });
});
