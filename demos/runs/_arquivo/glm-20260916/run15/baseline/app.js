"use strict";

const abas = Array.from(document.querySelectorAll(".aba"));
const formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

for (const aba of abas) {
  aba.addEventListener("click", () => {
    for (const outra of abas) outra.classList.toggle("ativa", outra === aba);
    for (const [nome, form] of Object.entries(formularios)) form.hidden = nome !== aba.dataset.aba;
  });
}

function formatarMoeda(bruto) {
  const digitos = bruto.replace(/\D/g, "");
  if (!digitos) return "";
  const centavos = digitos.slice(-2).padStart(2, "0");
  const inteiro = digitos.slice(0, -2).replace(/^0+/, "") || "0";
  return "R$ " + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
}

function formatarCpf(bruto) {
  const digitos = bruto.replace(/\D/g, "").slice(0, 11);
  const texto = [digitos.slice(0, 3), digitos.slice(3, 6), digitos.slice(6, 9)].filter(Boolean).join(".");
  const verificadores = digitos.slice(9, 11);
  return verificadores ? texto + "-" + verificadores : texto;
}

function formatarCep(bruto) {
  const digitos = bruto.replace(/\D/g, "").slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(bruto) {
  const digitos = bruto.replace(/\D/g, "").slice(0, 8);
  return [digitos.slice(0, 2), digitos.slice(2, 4), digitos.slice(4, 8)].filter(Boolean).join("/");
}

const FORMATADORES = [
  ["f-valor", formatarMoeda],
  ["f-cpf", formatarCpf],
  ["f-cep", formatarCep],
  ["f-data", formatarData],
];

for (const [classe, formatar] of FORMATADORES) {
  for (const campo of document.querySelectorAll("." + classe)) {
    const aplicar = () => { campo.value = formatar(campo.value); };
    campo.addEventListener("input", aplicar);
    campo.addEventListener("blur", aplicar);
  }
}

async function enviar(evento) {
  evento.preventDefault();
  const form = evento.currentTarget;
  const caixaDeErros = form.querySelector(".erros");
  const campos = {};
  for (const [nome, valor] of new FormData(form)) campos[nome] = String(valor).trim();
  campos["VALOR SOLICITADO (R$)"] = (campos["VALOR SOLICITADO (R$)"] || "").replace(/\D/g, "");
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/" },
    body: JSON.stringify({ aba: form.dataset.aba, campos: campos }),
  });
  const dados = await resposta.();
  caixaDeErros.replaceChildren();
  if (dados.valido) {
    document.getElementById("oficio").textContent = dados.oficio;
    document.getElementById("formulario").hidden = true;
    document.getElementById("confirmacao").hidden = false;
    window.scrollTo(0, 0);
  } else {
    for (const mensagem of dados.erros) {
      const item = document.createElement("p");
      item.textContent = mensagem;
      caixaDeErros.append(item);
    }
    caixaDeErros.hidden = false;
  }
}

for (const form of document.querySelectorAll("form.solicitacao")) {
  form.addEventListener("submit", enviar);
}
