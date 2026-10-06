"use strict";

function apenasDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function comMilhares(digitos) {
  return digitos.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function formatarValor(campo) {
  const d = apenasDigitos(campo.value);
  if (!d) {
    campo.value = "";
    return;
  }
  const centavos = d.slice(-2).padStart(2, "0");
  const reais = parseInt(d.slice(0, -2) || "0", 10).toString();
  campo.value = "R$ " + comMilhares(reais) + "," + centavos;
}

function formatarCpf(campo) {
  const d = apenasDigitos(campo.value);
  if (d.length === 11) {
    campo.value = d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  }
}

function formatarCep(campo) {
  const d = apenasDigitos(campo.value);
  if (d.length === 8) {
    campo.value = d.replace(/(\d{5})(\d{3})/, "$1-$2");
  }
}

function formatarData(campo) {
  const d = apenasDigitos(campo.value);
  if (d.length === 8) {
    campo.value = d.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
  }
}

const formatadores = {
  "VALOR SOLICITADO (R$)": formatarValor,
  "CPF (SEPARADOS POR PONTOS E TRAÇO)": formatarCpf,
  "CEP": formatarCep,
  "DATA DE NASCIMENTO": formatarData
};

for (const [nome, formatar] of Object.entries(formatadores)) {
  for (const campo of document.querySelectorAll(`input[name="${nome}"]`)) {
    campo.addEventListener("blur", () => formatar(campo));
  }
}

function abrirAba(nome) {
  for (const aba of document.querySelectorAll(".aba")) {
    aba.classList.toggle("ativa", aba.dataset.aba === nome);
  }
  for (const painel of document.querySelectorAll(".painel")) {
    painel.hidden = painel.dataset.aba !== nome;
  }
}

for (const aba of document.querySelectorAll(".aba")) {
  aba.addEventListener("click", () => abrirAba(aba.dataset.aba));
}

for (const form of document.querySelectorAll("form")) {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const quadroErros = form.querySelector(".erros");
    quadroErros.hidden = true;
    quadroErros.textContent = "";
    for (const [nome, formatar] of Object.entries(formatadores)) {
      for (const campo of form.querySelectorAll(`input[name="${nome}"]`)) {
        formatar(campo);
      }
    }
    const campos = {};
    new FormData(form).forEach((valor, nome) => {
      campos[nome] = valor;
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ aba: form.dataset.aba, campos: campos })
    });
    const dados = await resposta.();
    if (dados.erros && dados.erros.length > 0) {
      quadroErros.textContent = dados.erros.join("\n");
      quadroErros.hidden = false;
      return;
    }
    document.getElementById("formularios").hidden = true;
    document.getElementById("oficio").textContent = dados.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
}
