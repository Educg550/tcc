"use strict";

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const centavos = digitos(texto);
  if (!centavos) {
    return "";
  }
  const numero = (parseInt(centavos, 10) / 100).toFixed(2);
  const [inteira, decimais] = numero.split(".");
  return "R$ " + inteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + decimais;
}

function formatarCpf(texto) {
  const d = digitos(texto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(texto) {
  const d = digitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

const abas = document.querySelectorAll(".aba");
abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    document.querySelectorAll(".painel").forEach((painel) => {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll("[data-formato]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll("form").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const mensagens = formulario.querySelector(".mensagens");
    mensagens.innerHTML = "";
    const dados = Object.fromEntries(new FormData(formulario).entries());
    const resposta = await fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    const corpo = await resposta.text();
    if (resposta.ok) {
      document.querySelector(".abas").hidden = true;
      document.querySelectorAll(".painel").forEach((painel) => {
        painel.hidden = true;
      });
      const resultado = document.getElementById("resultado");
      resultado.innerHTML = corpo;
      resultado.hidden = false;
    } else {
      mensagens.innerHTML = corpo;
    }
    window.scrollTo(0, 0);
  });
});
