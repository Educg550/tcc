"use strict";

const formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};
const abas = document.querySelectorAll(".aba");

function mostrarAba(nome) {
  abas.forEach(aba => aba.classList.toggle("ativa", aba.dataset.aba === nome));
  for (const perfil of Object.keys(formularios)) {
    formularios[perfil].classList.toggle("oculto", perfil !== nome);
  }
}

abas.forEach(aba => aba.addEventListener("click", () => mostrarAba(aba.dataset.aba)));

function moeda(centavos) {
  const inteiro = Math.floor(centavos / 100);
  const centesimos = String(centavos % 100).padStart(2, "0");
  return "R$ " + inteiro.toLocaleString("pt-BR") + "," + centesimos;
}

function formatarValor(valor) {
  const digitos = valor.replace(/\D/g, "");
  return digitos ? moeda(parseInt(digitos, 10)) : "";
}

function formatarCPF(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 11);
  if (digitos.length !== 11) { return digitos; }
  return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." +
    digitos.slice(6, 9) + "-" + digitos.slice(9);
}

function formatarCEP(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 8);
  return digitos.length === 8 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 8);
  return digitos.length === 8
    ? digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4)
    : digitos;
}

const formatos = {
  valor_solicitado: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData,
};

for (const form of Object.values(formularios)) {
  form.addEventListener("submit", aoEnviar);
  for (const campo of form.querySelectorAll("input, textarea")) {
    const formato = formatos[campo.name];
    if (formato) {
      campo.addEventListener("blur", () => { campo.value = formato(campo.value); });
    }
  }
}

async function aoEnviar(evento) {
  evento.preventDefault();
  const form = evento.target;
  const erros = form.querySelector(".erros");
  erros.innerHTML = "";
  erros.hidden = true;
  const dados = { perfil: form.dataset.perfil };
  new FormData(form).forEach((valor, chave) => { dados[chave] = valor; });
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const corpo = await resposta.json();
  if (resposta.ok) {
    confirmar(corpo.oficio);
    return;
  }
  erros.innerHTML = corpo.erros.map(mensagem => "<p>" + mensagem + "</p>").join("");
  erros.hidden = false;
}

function confirmar(oficio) {
  document.querySelector(".abas").hidden = true;
  document.getElementById("formularios").hidden = true;
  document.getElementById("confirmacao").hidden = false;
  document.getElementById("oficio").textContent = oficio;
  window.scrollTo(0, 0);
}
