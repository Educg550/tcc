"use strict";

function soDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

function mascaraValor(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) {
    return "";
  }
  const completos = digitos.padStart(3, "0");
  const reais = completos.slice(0, -2);
  const centavos = completos.slice(-2);
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
}

function mascaraCpf(valor) {
  const digitos = soDigitos(valor).slice(0, 11);
  let saida = digitos.slice(0, 3);
  if (digitos.length > 3) {
    saida += "." + digitos.slice(3, 6);
  }
  if (digitos.length > 6) {
    saida += "." + digitos.slice(6, 9);
  }
  if (digitos.length > 9) {
    saida += "-" + digitos.slice(9);
  }
  return saida;
}

function mascaraCep(valor) {
  const digitos = soDigitos(valor).slice(0, 8);
  return digitos.length <= 5 ? digitos : digitos.slice(0, 5) + "-" + digitos.slice(5);
}

function mascaraData(valor) {
  const digitos = soDigitos(valor).slice(0, 8);
  if (digitos.length <= 2) {
    return digitos;
  }
  if (digitos.length <= 4) {
    return digitos.slice(0, 2) + "/" + digitos.slice(2);
  }
  return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
}

const MASCARAS = {
  valor: mascaraValor,
  cpf: mascaraCpf,
  cep: mascaraCep,
  data: mascaraData,
};

document.querySelectorAll("[data-mascara]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = MASCARAS[campo.dataset.mascara](campo.value);
  });
});

const paineis = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    Object.entries(paineis).forEach(([nome, painel]) => {
      painel.hidden = nome !== aba.dataset.aba;
    });
  });
});

function enviarFormulario(form, tipo) {
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const erros = form.querySelector(".erros");
    erros.innerHTML = "";
    erros.hidden = true;
    const dados = { tipo: tipo };
    form.querySelectorAll("[name]").forEach((campo) => {
      dados[campo.name] = campo.value.trim();
    });
    fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then((resposta) => resposta.json())
      .then((corpo) => {
        if (corpo.ok) {
          document.getElementById("oficio").textContent = corpo.oficio;
          document.getElementById("formulario").hidden = true;
          document.getElementById("confirmacao").hidden = false;
          return;
        }
        corpo.erros.forEach((mensagem) => {
          const linha = document.createElement("p");
          linha.textContent = mensagem;
          erros.appendChild(linha);
        });
        erros.hidden = false;
      });
  });
}

enviarFormulario(paineis.alunos, "aluno");
enviarFormulario(paineis.docentes, "docente");
