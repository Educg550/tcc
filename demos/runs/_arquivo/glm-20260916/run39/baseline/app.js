"use strict";

function apenasDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarValor(valor) {
  const digitos = apenasDigitos(valor);
  if (!digitos) {
    return "";
  }
  const texto = digitos.padStart(3, "0");
  const reais = texto.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + texto.slice(-2);
}

function formatarCpf(valor) {
  const d = apenasDigitos(valor).slice(0, 11);
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

function formatarCep(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  if (d.length <= 5) {
    return d;
  }
  return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
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
  data: formatarData
};

document.querySelectorAll("[data-formato]").forEach((campo) => {
  const formatar = FORMATADORES[campo.dataset.formato];
  campo.addEventListener("input", () => {
    if (campo.selectionStart === campo.value.length) {
      campo.value = formatar(campo.value);
    }
  });
  campo.addEventListener("blur", () => {
    campo.value = formatar(campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".form").forEach((formulario) => {
      formulario.hidden = formulario.dataset.perfil !== aba.dataset.aba;
    });
  });
});

async function enviar(formulario) {
  const dados = Object.fromEntries(new FormData(formulario));
  dados.perfil = formulario.dataset.perfil;
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/" },
    body: JSON.stringify(dados)
  });
  const resultado = await resposta.();
  if (!resultado.ok) {
    const quadro = formulario.querySelector(".erros");
    quadro.replaceChildren();
    resultado.erros.forEach((mensagem) => {
      const linha = document.createElement("p");
      linha.textContent = mensagem;
      quadro.appendChild(linha);
    });
    quadro.hidden = false;
    return;
  }
  document.getElementById("abas").hidden = true;
  document.getElementById("formulario").hidden = true;
  document.getElementById("oficio").textContent = resultado.oficio;
  document.getElementById("confirmacao").hidden = false;
}

document.querySelectorAll(".form").forEach((formulario) => {
  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviar(formulario);
  });
});
