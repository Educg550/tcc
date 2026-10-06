"use strict";

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function apenasDigitos(texto) {
  return texto.replace(/[^0-9]/g, "");
}

function formatarMoeda(texto) {
  const digitos = apenasDigitos(texto);
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCpf(texto) {
  const digitos = apenasDigitos(texto).slice(0, 11);
  let formatado = digitos.slice(0, 3);
  if (digitos.length > 3) formatado += "." + digitos.slice(3, 6);
  if (digitos.length > 6) formatado += "." + digitos.slice(6, 9);
  if (digitos.length > 9) formatado += "-" + digitos.slice(9, 11);
  return formatado;
}

function formatarCep(texto) {
  const digitos = apenasDigitos(texto).slice(0, 8);
  let formatado = digitos.slice(0, 5);
  if (digitos.length > 5) formatado += "-" + digitos.slice(5, 8);
  return formatado;
}

function formatarData(texto) {
  const digitos = apenasDigitos(texto).slice(0, 8);
  let formatado = digitos.slice(0, 2);
  if (digitos.length > 2) formatado += "/" + digitos.slice(2, 4);
  if (digitos.length > 4) formatado += "/" + digitos.slice(4, 8);
  return formatado;
}

function configurarAbas() {
  const abas = document.querySelectorAll(".aba");
  abas.forEach((aba) => {
    aba.addEventListener("click", () => {
      abas.forEach((outra) => {
        const ativa = outra === aba;
        outra.classList.toggle("ativa", ativa);
        outra.setAttribute("aria-selected", ativa ? "true" : "false");
        document.getElementById(outra.dataset.alvo).hidden = !ativa;
      });
    });
  });
}

function configurarFormatos() {
  document.querySelectorAll("[data-formato]").forEach((campo) => {
    campo.addEventListener("blur", () => {
      campo.value = FORMATADORES[campo.dataset.formato](campo.value);
    });
  });
}

function configurarEnvios() {
  document.querySelectorAll("form.solicitacao").forEach((formulario) => {
    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const quadroDeErros = formulario.querySelector(".erros");
      quadroDeErros.replaceChildren();
      const payload = { tipo: formulario.dataset.tipo };
      formulario.querySelectorAll("[name]").forEach((campo) => {
        let valor = campo.value;
        if (campo.dataset.formato === "moeda") {
          valor = apenasDigitos(valor);
        }
        payload[campo.name] = valor;
      });
      const resposta = await fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/" },
        body: JSON.stringify(payload),
      });
      const conteudo = await resposta.();
      if (typeof conteudo.oficio === "string") {
        document.getElementById("oficio").textContent = conteudo.oficio;
        document.getElementById("formularios").hidden = true;
        document.getElementById("confirmacao").hidden = false;
        window.scrollTo(0, 0);
        return;
      }
      (conteudo.erros || []).forEach((mensagem) => {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        quadroDeErros.appendChild(linha);
      });
    });
  });
}

configurarAbas();
configurarFormatos();
configurarEnvios();
