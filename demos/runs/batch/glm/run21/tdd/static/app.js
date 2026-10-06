// Comportamento de tela: abas, máscaras e envio das solicitações.
"use strict";

const TABS = [
  { id: "alunos", botao: document.getElementById("tab-alunos"), form: document.getElementById("form-alunos"), erros: document.getElementById("erros-alunos") },
  { id: "docentes", botao: document.getElementById("tab-docentes"), form: document.getElementById("form-docentes"), erros: document.getElementById("erros-docentes") },
];

function ativarAba(aba) {
  for (const t of TABS) {
    const ativa = t.id === aba;
    t.botao.classList.toggle("ativa", ativa);
    t.form.classList.toggle("visivel", ativa);
    t.form.classList.toggle("oculto", !ativa);
  }
}

for (const t of TABS) {
  t.botao.addEventListener("click", () => ativarAba(t.id));
}

ativarAba("alunos");

// ---------------------------------------------------------------------------
// Máscaras aplicadas quando o usuário sai do campo
// ---------------------------------------------------------------------------

function moedaDigitada(texto) {
  const digitos = texto.replace(/\D/g, "");
  if (!digitos) return "";
  const valor = parseInt(digitos, 10);
  const centavos = String(valor % 100).padStart(2, "0");
  let inteiro = String(Math.floor(valor / 100));
  const partes = [];
  while (inteiro.length > 3) {
    partes.unshift(inteiro.slice(-3));
    inteiro = inteiro.slice(0, -3);
  }
  partes.unshift(inteiro);
  return "R$ " + partes.join(".") + "," + centavos;
}

function cpfDigitado(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 11);
  return d.length === 11 ? `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}` : texto;
}

function cepDigitado(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 8);
  return d.length === 8 ? `${d.slice(0, 5)}-${d.slice(5)}` : texto;
}

function dataDigitada(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 8);
  return d.length === 8 ? `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}` : texto;
}

const MASCARAS = {
  valor_solicitado: moedaDigitada,
  cpf: cpfDigitado,
  cep: cepDigitado,
  data_de_nascimento: dataDigitada,
};

for (const form of TABS.map((t) => t.form)) {
  for (const [id, mascara] of Object.entries(MASCARAS)) {
    const campo = form.querySelector("#" + id);
    if (!campo) continue;
    campo.addEventListener("blur", () => {
      campo.value = mascara(campo.value);
    });
  }

  // Ofício gerado no backend precisa do valor em centavos:
  // o campo formatado volta a ser só dígitos antes do envio.
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const valor = form.querySelector("#valor_solicitado");
    if (valor) valor.value = valor.value.replace(/\D/g, "");
    enviar(form);
  });
}

// ---------------------------------------------------------------------------
// Envio e resposta
// ---------------------------------------------------------------------------

function coletarDados(form) {
  const dados = { aba: form.dataset.aba };
  for (const campo of form.querySelectorAll("input, select, textarea")) {
    dados[campo.name] = campo.value;
  }
  return dados;
}

function mostrarErros(aba, erros) {
  const bloco = TABS.find((t) => t.id === aba).erros;
  bloco.innerHTML = "";
  for (const mensagem of erros) {
    const item = document.createElement("li");
    item.textContent = mensagem;
    bloco.appendChild(item);
  }
}

async function enviar(form) {
  const aba = form.dataset.aba;
  mostrarErros(aba, []);
  const resposta = await fetch("/api/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(coletarDados(form)),
  });
  const corpo = await resposta.json();
  if (!resposta.ok) {
    mostrarErros(aba, corpo.erros || []);
    return;
  }
  document.getElementById("oficio").textContent = corpo.oficio;
  for (const t of TABS) {
    t.form.classList.add("oculto");
    t.form.classList.remove("visivel");
    t.botao.classList.add("oculto");
  }
  document.querySelector(".abas").classList.add("oculto");
  document.getElementById("confirmacao").classList.remove("oculto");
  document.querySelector("#confirmacao .titulo").scrollIntoView();
}
