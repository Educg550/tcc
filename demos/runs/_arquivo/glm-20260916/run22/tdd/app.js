"use strict";

function apenasDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const digitos = apenasDigitos(texto).slice(0, 12);
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCpf(texto) {
  const d = apenasDigitos(texto).slice(0, 11);
  if (d.length > 9) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }
  if (d.length > 6) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  }
  if (d.length > 3) {
    return d.slice(0, 3) + "." + d.slice(3);
  }
  return d;
}

function formatarCep(texto) {
  const d = apenasDigitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(texto) {
  const d = apenasDigitos(texto).slice(0, 8);
  if (d.length > 4) {
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }
  if (d.length > 2) {
    return d.slice(0, 2) + "/" + d.slice(2);
  }
  return d;
}

const FORMATACAO = [
  [".campo-moeda", formatarMoeda],
  [".campo-cpf", formatarCpf],
  [".campo-cep", formatarCep],
  [".campo-data", formatarData],
];

for (const [seletor, formatar] of FORMATACAO) {
  for (const campo of document.querySelectorAll(seletor)) {
    campo.addEventListener("blur", () => {
      campo.value = formatar(campo.value);
    });
  }
}

const abas = Array.from(document.querySelectorAll(".aba"));

for (const aba of abas) {
  aba.addEventListener("click", () => {
    for (const outra of abas) {
      const formulario = document.getElementById(outra.dataset.form);
      outra.classList.toggle("ativa", outra === aba);
      formulario.hidden = outra !== aba;
    }
  });
}

function dadosDaSolicitacao(form) {
  const dados = Object.fromEntries(new FormData(form).entries());
  if (form.id === "form-alunos") {
    dados["NÍVEL"] = dados.nivel;
    dados["TIPO DE AUXÍLIO"] = dados.tipoAuxilio;
  }
  delete dados.nivel;
  delete dados.tipoAuxilio;
  dados["ABA"] = form.id === "form-alunos" ? "ALUNOS" : "DOCENTES";
  return dados;
}

for (const form of document.querySelectorAll("form")) {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dadosDaSolicitacao(form))
    });
    const corpo = await resposta.();
    const caixaDeErros = form.querySelector(".erros");
    if (corpo.erros) {
      caixaDeErros.textContent = corpo.erros.join("\n");
      caixaDeErros.hidden = false;
      return;
    }
    document.getElementById("abas").hidden = true;
    document.getElementById("formularios").hidden = true;
    document.getElementById("oficio").textContent = corpo.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
}
