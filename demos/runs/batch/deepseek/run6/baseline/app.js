"use strict";

function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formataValor(valor) {
  let digitos = soDigitos(valor).replace(/^0+(?=\d)/, "");
  if (digitos === "") return "";
  digitos = digitos.padStart(3, "0");
  const reais = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + digitos.slice(-2);
}

function formataCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formataCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formataData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const FORMATADORES = {
  valor: formataValor,
  cpf: formataCpf,
  cep: formataCep,
  nascimento: formataData
};

document.querySelectorAll(".painel input[name]").forEach(function (campo) {
  const formata = FORMATADORES[campo.name];
  if (!formata) return;
  campo.addEventListener("blur", function () {
    campo.value = formata(campo.value);
  });
});

const abas = Array.from(document.querySelectorAll(".aba"));
const paineis = Array.from(document.querySelectorAll("form.painel"));

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    paineis.forEach(function (painel) {
      painel.classList.toggle("ativa", painel.dataset.aba === aba.dataset.aba);
    });
  });
});

paineis.forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    const dados = { aba: form.dataset.aba };
    form.querySelectorAll("input[name], select[name], textarea[name]").forEach(function (campo) {
      dados[campo.name] = campo.value;
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.json();
    const caixa = form.querySelector(".erros");

    if (resultado.ok) {
      caixa.hidden = true;
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("painel-solicitacao").hidden = true;
      document.getElementById("confirmacao").hidden = false;
      window.scrollTo(0, 0);
      return;
    }

    caixa.textContent = "";
    resultado.erros.forEach(function (mensagem) {
      const linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  });
});
