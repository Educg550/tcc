"use strict";

const digitos = (valor) => valor.replace(/\D/g, "");

function formatarValor(valor) {
  const centavos = digitos(valor);
  if (!centavos) return "";
  const inteiro = Math.floor(Number(centavos) / 100).toLocaleString("pt-BR");
  const resto = String(Number(centavos) % 100).padStart(2, "0");
  return `R$ ${inteiro},${resto}`;
}

function formatarCPF(valor) {
  const d = digitos(valor).slice(0, 11);
  let cpf = d.slice(0, 3);
  if (d.length > 3) cpf += "." + d.slice(3, 6);
  if (d.length > 6) cpf += "." + d.slice(6, 9);
  if (d.length > 9) cpf += "-" + d.slice(9, 11);
  return cpf;
}

function formatarCEP(valor) {
  const d = digitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  const d = digitos(valor).slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += "/" + d.slice(2, 4);
  if (d.length > 4) saida += "/" + d.slice(4, 8);
  return saida;
}

function aplicarMascaras(form) {
  form.valor.addEventListener("blur", () => { form.valor.value = formatarValor(form.valor.value); });
  form.cpf.addEventListener("blur", () => { form.cpf.value = formatarCPF(form.cpf.value); });
  form.cep.addEventListener("blur", () => { form.cep.value = formatarCEP(form.cep.value); });
  form.nascimento.addEventListener("blur", () => { form.nascimento.value = formatarData(form.nascimento.value); });
}

function trocarAba(alvo) {
  for (const aba of abaBotoes) aba.classList.toggle("ativa", aba.dataset.aba === alvo);
  for (const painel of paineis) painel.classList.toggle("ativa", painel.dataset.aba === alvo);
}

const abaBotoes = document.querySelectorAll(".aba");
const paineis = document.querySelectorAll(".painel");
const paginaForm = document.getElementById("cadastrar");
const paginaOk = document.getElementById("confirmacao");
const erroServidor = document.getElementById("erro-servidor");

abaBotoes.forEach((aba) => aba.addEventListener("click", () => trocarAba(aba.dataset.aba)));

function montarPayload(form) {
  const dados = { perfil: form.dataset.aba };
  for (const campo of form.querySelectorAll("input, select, textarea")) {
    dados[campo.name] = campo.value;
  }
  return dados;
}

async function enviar(form) {
  const caixa = form.querySelector(".erros");
  caixa.replaceChildren();
  erroServidor.hidden = true;
  try {
    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(montarPayload(form)),
    });
    const resultado = await resposta.json();
    if (!resultado.ok) {
      for (const msg of resultado.erros) {
        const p = document.createElement("p");
        p.textContent = msg;
        caixa.append(p);
      }
      return;
    }
    document.getElementById("oficio").textContent = resultado.oficio;
    paginaForm.hidden = true;
    paginaOk.hidden = false;
  } catch (e) {
    erroServidor.textContent = "Falha de comunicação com o servidor. Tente novamente.";
    erroServidor.hidden = false;
  }
}

for (const form of document.querySelectorAll("form.painel")) {
  aplicarMascaras(form);
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviar(form);
  });
}
