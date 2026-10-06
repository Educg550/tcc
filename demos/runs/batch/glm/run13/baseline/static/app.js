// Comportamento de tela da solicitação de auxílio financeiro.

const $ = (sel, raiz = document) => raiz.querySelector(sel);
const $$ = (sel, raiz = document) => [...raiz.querySelectorAll(sel)];

const digitos = (texto) => (texto.match(/\d/g) || []).join("");

function formatarMoeda(bruto) {
  const centavos = digitos(bruto).replace(/^0+(?=\d)/, "");
  if (!centavos) return "";
  const inteiro = centavos.slice(0, -2) || "0";
  const parte = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${parte},${centavos.slice(-2).padStart(2, "0")}`;
}

function formatarCPF(bruto) {
  const d = digitos(bruto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

function formatarCEP(bruto) {
  const d = digitos(bruto).slice(0, 8);
  if (d.length <= 5) return d;
  return `${d.slice(0, 5)}-${d.slice(5)}`;
}

function formatarData(bruto) {
  const d = digitos(bruto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

const formatadores = {
  valor_solicitado: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData,
};

$$("input[name]").forEach((campo) => {
  const formatar = formatadores[campo.name];
  if (!formatar) return;
  campo.addEventListener("blur", () => {
    const texto = formatar(campo.value);
    campo.value = texto;
    campo.dataset.centavos = campo.name === "valor_solicitado" ? digitos(texto) : "";
  });
});

$$("button.aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    $$("button.aba").forEach((b) => b.classList.toggle("ativa", b === botao));
    const alvo = botao.dataset.aba;
    $$("form.painel").forEach((form) => {
      form.hidden = form.dataset.aba !== alvo;
    });
  });
});

function coletar(form) {
  const dados = { tipo: form.dataset.aba };
  new FormData(form).forEach((valor, nome) => {
    dados[nome] = valor.toString().trim();
  });
  const valor = form.querySelector("[name=valor_solicitado]");
  dados.valor_solicitado = valor ? Number(digitos(valor.value)) / 100 : 0;
  return dados;
}

async function enviar(evento) {
  evento.preventDefault();
  const form = evento.currentTarget;
  const erro = form.querySelector(".erros");
  erro.hidden = true;
  erro.textContent = "";
  try {
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletar(form)),
    });
    const dados = await resposta.json();
    if (!dados.ok) {
      erro.textContent = dados.erros.join("\n");
      erro.hidden = false;
      return;
    }
    $("#oficio").textContent = dados.oficio;
    form.hidden = true;
    $("main.conteudo").hidden = true;
    $("#confirmacao").hidden = false;
  } catch {
    erro.textContent = "Não foi possível enviar a solicitação.";
    erro.hidden = false;
  }
}

$$("form.painel").forEach((form) => form.addEventListener("submit", enviar));

$("#nova").addEventListener("click", () => {
  $("#confirmacao").hidden = true;
  $("main.conteudo").hidden = false;
  const ativa = $("button.aba.ativa").dataset.aba;
  $(`form.painel[data-aba=${ativa}]`).hidden = false;
});
