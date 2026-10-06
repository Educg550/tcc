"use strict";

const ABAS = ["alunos", "docentes"];
const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(campo) {
  const d = digitos(campo.value);
  if (!d) {
    campo.value = "";
    return;
  }
  const n = d.replace(/^0+/, "") || "0";
  const centavos = n.slice(-2).padStart(2, "0");
  const reais = (n.slice(0, -2) || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  campo.value = "R$ " + reais + "," + centavos;
}

function formatarCPF(campo) {
  const d = digitos(campo.value).slice(0, 11);
  if (!d) {
    campo.value = "";
    return;
  }
  const partes = [d.slice(0, 3), d.slice(3, 6), d.slice(6, 9), d.slice(9)].filter(Boolean);
  campo.value = partes.length === 4
    ? partes.slice(0, 3).join(".") + "-" + partes[3]
    : partes.join(".");
}

function formatarCEP(campo) {
  const d = digitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(campo) {
  const d = digitos(campo.value).slice(0, 8);
  campo.value = d.length > 4
    ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4)
    : d.length > 2 ? d.slice(0, 2) + "/" + d.slice(2) : d;
}

for (const campo of document.querySelectorAll("[data-formato]")) {
  const formatar = FORMATADORES[campo.dataset.formato];
  campo.addEventListener("input", () => formatar(campo));
  campo.addEventListener("blur", () => formatar(campo));
}

function abrirAba(nome) {
  for (const aba of ABAS) {
    document.getElementById("aba-" + aba).classList.toggle("ativa", aba === nome);
    document.getElementById("form-" + aba).hidden = aba !== nome;
  }
}

for (const aba of ABAS) {
  document.getElementById("aba-" + aba).addEventListener("click", () => abrirAba(aba));
}

function mostrarErros(caixa, mensagens) {
  caixa.replaceChildren(...mensagens.map((mensagem) => {
    const item = document.createElement("div");
    item.textContent = mensagem;
    return item;
  }));
  caixa.hidden = false;
}

for (const aba of ABAS) {
  const form = document.getElementById("form-" + aba);
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { aba: aba };
    for (const campo of form.querySelectorAll("[name]")) {
      dados[campo.name] = campo.name === "valor" ? digitos(campo.value) : campo.value.trim();
    }
    const caixa = form.querySelector(".erros");
    let resposta;
    try {
      resposta = await fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/" },
        body: JSON.stringify(dados),
      });
    } catch {
      mostrarErros(caixa, ["Não foi possível enviar a solicitação."]);
      return;
    }
    const r = await resposta.();
    if (r.ok) {
      document.getElementById("form-view").hidden = true;
      document.getElementById("oficio").textContent = r.oficio;
      document.getElementById("confirm-view").hidden = false;
    } else {
      mostrarErros(caixa, r.erros);
    }
  });
}
