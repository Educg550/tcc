"use strict";

const OPCOES_NIVEL = ["Mestrado", "Doutorado"];
const OPCOES_TIPO = ["Participação em evento", "Banca de exame ou defesa", "Outro"];
const OPCOES_APRESENTACAO = ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"];

function buildSelect(id, values) {
  const select = document.getElementById(id);
  if (select) {
    for (const value of values) {
      const option = document.createElement("option");
      option.textContent = value;
      select.appendChild(option);
    }
  }
}

buildSelect("a-nivel", OPCOES_NIVEL);
buildSelect("a-tipo", OPCOES_TIPO);
buildSelect("a-apresentacao", OPCOES_APRESENTACAO);
buildSelect("d-apresentacao", OPCOES_APRESENTACAO);

const digitos = (value) => value.replace(/\D/g, "");

function formatCurrency(digits) {
  if (!digits) return "";
  const cents = digits.replace(/^0+/, "") || "0";
  const part = cents.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const formatted = part.length > 2 ? `${part.slice(0, -2)},${part.slice(-2)}` : `0,${part.padStart(2, "0")}`;
  return `R$ ${formatted}`;
}

function formatCPF(digits) {
  if (digits.length > 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9, 11)}`;
  if (digits.length > 6) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  if (digits.length > 3) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  return digits;
}

function formatCEP(digits) {
  return digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5, 8)}` : digits;
}

function formatDate(digits) {
  if (digits.length > 4) return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4, 8)}`;
  if (digits.length > 2) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return digits;
}

const formatters = {
  "valor-solicitado": (digits) => formatCurrency(digits),
  cpf: (digits) => formatCPF(digits),
  cep: (digits) => formatCEP(digits),
  "data-nascimento": (digits) => formatDate(digits),
};

for (const [name, formatter] of Object.entries(formatters)) {
  for (const form of document.querySelectorAll("form")) {
    const field = form.elements[name];
    if (field) {
      field.addEventListener("blur", () => {
        const digits = digitos(field.value);
        if (digits.length === 0) {
          field.value = "";
          return;
        }
        field.value = formatter(digits);
      });
    }
  }
}

const abaAtiva = () => document.querySelector("#abas .aba.ativa").dataset.aba;

for (const button of document.querySelectorAll("#abas .aba")) {
  button.addEventListener("click", () => {
    for (const b of document.querySelectorAll("#abas .aba")) b.classList.remove("ativa");
    button.classList.add("ativa");
    for (const form of document.querySelectorAll("form")) {
      form.hidden = form.dataset.aba !== button.dataset.aba;
    }
  });
}

for (const form of document.querySelectorAll("form")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = { aba: form.dataset.aba };
    for (const field of form.querySelectorAll("input, select, textarea")) {
      payload[field.name] = field.value;
    }
    const response = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    const errorBox = form.parentElement.querySelector(".erros");
    errorBox.innerHTML = "";
    if (data.erros && data.erros.length > 0) {
      errorBox.hidden = false;
      for (const message of data.erros) {
        const p = document.createElement("p");
        p.textContent = message;
        errorBox.appendChild(p);
      }
      return;
    }
    errorBox.hidden = true;
    document.getElementById("pagina").hidden = true;
    const confirm = document.getElementById("confirmacao");
    confirm.classList.remove("oculto");
    confirm.hidden = false;
    document.getElementById("oficio").textContent = data.oficio;
    window.scrollTo(0, 0);
  });
}
