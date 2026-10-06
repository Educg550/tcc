"use strict";

const paineis = {
  alunos: document.getElementById("painel-alunos"),
  docentes: document.getElementById("painel-docentes"),
};
const pagina = document.getElementById("pagina-formulario");
const confirmacao = document.getElementById("confirmacao");
const oficio = document.getElementById("oficio");

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    const nome = aba.dataset.aba;
    document.querySelectorAll(".aba").forEach((botao) => {
      botao.classList.toggle("ativa", botao === aba);
    });
    Object.keys(paineis).forEach((chave) => {
      paineis[chave].hidden = chave !== nome;
    });
  });
});

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(digitos) {
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${reais},${String(centavos % 100).padStart(2, "0")}`;
}

function formatarCpf(digitos) {
  const d = digitos.slice(0, 11);
  let texto = d.slice(0, 3);
  if (d.length > 3) {
    texto += `.${d.slice(3, 6)}`;
  }
  if (d.length > 6) {
    texto += `.${d.slice(6, 9)}`;
  }
  if (d.length > 9) {
    texto += `-${d.slice(9)}`;
  }
  return texto;
}

function formatarCep(digitos) {
  const d = digitos.slice(0, 8);
  return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}

function formatarData(digitos) {
  const d = digitos.slice(0, 8);
  let texto = d.slice(0, 2);
  if (d.length > 2) {
    texto += `/${d.slice(2, 4)}`;
  }
  if (d.length > 4) {
    texto += `/${d.slice(4)}`;
  }
  return texto;
}

const mascaras = [
  ["js-moeda", formatarMoeda],
  ["js-cpf", formatarCpf],
  ["js-cep", formatarCep],
  ["js-data", formatarData],
];

mascaras.forEach(([classe, formatar]) => {
  document.querySelectorAll(`.${classe}`).forEach((campo) => {
    campo.addEventListener("blur", () => {
      campo.value = formatar(soDigitos(campo.value));
    });
  });
});

document.querySelectorAll("form.formulario").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(formulario).entries());
    dados.aba = formulario.dataset.aba;
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.json();
    const lista = formulario.querySelector(".erros");
    lista.innerHTML = "";
    const erros = corpo.erros || [];
    erros.forEach((mensagem) => {
      const item = document.createElement("li");
      item.textContent = mensagem;
      lista.appendChild(item);
    });
    if (erros.length > 0) {
      return;
    }
    oficio.textContent = corpo.oficio;
    pagina.hidden = true;
    confirmacao.hidden = false;
  });
});
