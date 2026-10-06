"use strict";

const abas = document.querySelectorAll(".aba");
const paineis = document.querySelectorAll(".painel");

abas.forEach((botao) => {
  botao.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === botao));
    const alvo = "painel-" + botao.dataset.aba;
    paineis.forEach((painel) => {
      painel.hidden = painel.id !== alvo;
    });
  });
});

function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarValor(valor) {
  const d = soDigitos(valor);
  if (!d) return "";
  const n = BigInt(d);
  const centavos = (n % 100n).toString().padStart(2, "0");
  const reais = (n / 100n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + centavos;
}

function formatarCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function formatarCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

const formatadores = [
  ["fmt-valor", formatarValor],
  ["fmt-cpf", formatarCpf],
  ["fmt-cep", formatarCep],
  ["fmt-data", formatarData],
];

document.addEventListener("focusout", (evento) => {
  const campo = evento.target;
  if (!campo.classList) return;
  for (const [classe, formatar] of formatadores) {
    if (campo.classList.contains(classe)) {
      campo.value = formatar(campo.value);
      return;
    }
  }
});

async function enviarSolicitacao(aba, formulario) {
  const corpo = new URLSearchParams();
  corpo.set("aba", aba);
  formulario.querySelectorAll("input, select, textarea").forEach((campo) => {
    corpo.set(campo.name, campo.value.trim());
  });
  const caixaErros = document.getElementById("erros-" + aba);
  caixaErros.hidden = true;
  caixaErros.replaceChildren();
  const resposta = await fetch("/api/solicitacao", { method: "POST", body: corpo });
  const  = await resposta.();
  if (.ok) {
    document.getElementById("oficio").textContent = .oficio;
    paineis.forEach((painel) => {
      painel.hidden = painel.id !== "confirmacao";
    });
  } else {
    for (const mensagem of .erros) {
      const paragrafo = document.createElement("p");
      paragrafo.textContent = mensagem;
      caixaErros.appendChild(paragrafo);
    }
    caixaErros.hidden = false;
  }
}

document.getElementById("form-alunos").addEventListener("submit", (evento) => {
  evento.preventDefault();
  enviarSolicitacao("alunos", evento.target);
});

document.getElementById("form-docentes").addEventListener("submit", (evento) => {
  evento.preventDefault();
  enviarSolicitacao("docentes", evento.target);
});
