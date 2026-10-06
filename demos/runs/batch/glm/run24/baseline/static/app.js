// Comportamento de tela: abas, máscaras de digitação e envio das solicitações.
"use strict";

const ABAS = [
  { id: "alunos", botao: document.getElementById("tab-alunos"), painel: document.getElementById("form-alunos") },
  { id: "docentes", botao: document.getElementById("tab-docentes"), painel: document.getElementById("form-docentes") },
];

let abaAtiva = "alunos";

function trocarAba(id) {
  abaAtiva = id;
  for (const aba of ABAS) {
    const visivel = aba.id === id;
    aba.painel.hidden = !visivel;
    aba.botao.classList.toggle("ativa", visivel);
    aba.botao.setAttribute("aria-selected", String(visivel));
  }
}

for (const aba of ABAS) aba.botao.addEventListener("click", () => trocarAba(aba.id));

// ---------------------------------------------------------------------------
// Máscaras: reformatam o que foi digitado quando o usuário sai do campo.
// ---------------------------------------------------------------------------

function formatarMoeda(digitos) {
  let centavos = digitos.replace(/\D/g, "");
  if (centavos === "") return "";
  let inteiro = centavos.slice(0, -2) || "0";
  const frac = centavos.slice(-2).padStart(2, "0");
  inteiro = String(Number(inteiro)); // remove zeros à esquerda
  const grupos = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${grupos},${frac}`;
}

function formatarCpf(digitos) {
  const d = digitos.replace(/\D/g, "").slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

function formatarCep(digitos) {
  const d = digits.slice(0, 8);
  return d.length <= 5 ? d : `${d.slice(0, 5)}-${d.slice(5)}`;
}

function formatarData(digitos) {
  const d = digits.slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

const MASCARAS = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

for (const campo of document.querySelectorAll("input.moeda, input.cpf, input.cep, input.data")) {
  campo.addEventListener("blur", () => {
    const formatar = MASCARAS[campo.classList[0]] || MASCARAS[campo.className];
    const texto = formatar(campo.value);
    if (texto !== campo.value) {
      campo.value = texto;
      campo.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });
}

// ---------------------------------------------------------------------------
// Envio e tratamento da resposta do backend.
// ---------------------------------------------------------------------------

for (const aba of ABAS) {
  const form = aba.painel.querySelector("form");
  const erros = aba.painel.querySelector(".erros");

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(form).entries());
    dados.tipo = aba.id;
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    erros.innerHTML = "";
    if (resultado.ok) {
      const tpl = document.getElementById("tpl-ok");
      document.body.replaceChildren(tpl.content.cloneNode(true));
      document.getElementById("oficio").textContent = resultado.oficio;
      window.scrollTo(0, 0);
      return;
    }
    erros.hidden = false;
    for (const msg of resultado.erros) {
      const p = document.createElement("p");
      p.textContent = msg;
      erros.appendChild(p);
    }
    erros.scrollIntoView({ block: "start" });
  });
}
