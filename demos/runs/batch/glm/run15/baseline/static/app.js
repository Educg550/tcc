// Auxílio Financeiro - Pós-Graduação IME-USP

const VALOR = "VALOR SOLICITADO (R$)";
const CPF = "CPF (SEPARADOS POR PONTOS E TRAÇO)";
const CEP = "CEP";
const DATA = "DATA DE NASCIMENTO";

const OPCIONAIS = new Set(["LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"]);
const BLOCOS = ["solicitante", "endereco", "pagamento"];

function formataValor(texto) {
  const digitos = (texto.match(/\d/g) || []).join("").slice(0, 15);
  if (!digitos) return "";
  const centavos = digitos.padStart(3, "0");
  const reais = centavos.slice(0, -2);
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos.slice(-2);
}

function formataCpf(texto) {
  const d = (texto.match(/\d/g) || []).join("").slice(0, 11);
  return d
    .padStart(3, ".")
    .replace(/^(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})$/, "$1.$2.$3-$4")
    .replace(/\.$/, "")
    .replace(/\.\.$/, ".")
    .replace(/-$/, "");
}

function formataCep(texto) {
  const d = (texto.match(/\d/g) || []).join("").slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formataData(texto) {
  const d = (texto.match(/\d/g) || []).join("").slice(0, 8);
  const partes = [d.slice(0, 2), d.slice(2, 4), d.slice(4, 8)].filter(Boolean);
  return partes.join("/");
}

function aoSairDoCampo(campo) {
  const digitos = (campo.value.match(/\d/g) || []).join("");
  if (!digitos) return;
  if (campo.name === VALOR) campo.value = formataValor(digitos);
  if (campo.name === CPF) campo.value = formataCpf(digitos);
  if (campo.name === CEP) campo.value = formataCep(digitos);
  if (campo.name === DATA) campo.value = formataData(digitos);
}

document.addEventListener("blur", (evento) => {
  if (evento.target instanceof HTMLInputElement) aoSairDoCampo(evento.target);
}, true);

function blocoDoCampo(nome) {
  if (nome === DATA || ["LOGRADOURO", "NÚMERO", "COMPLEMENTO", "BAIRRO", CEP, "CIDADE", "ESTADO"].includes(nome)) return "endereco";
  if ([CPF, "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "NOME DO BANCO", "NÚMERO DA AGÊNCIA", "NÚMERO DA CONTA"].includes(nome)) return "pagamento";
  return "solicitante";
}

async function envia(formulario, aba) {
  const corpo = { perfil: aba, solicitante: {}, endereco: {}, pagamento: {} };
  for (const campo of formulario.elements) {
    if (!campo.name) continue;
    corpo[blocoDoCampo(campo.name)][campo.name] = { valor: campo.value, vazio: campo.value.trim() === "" };
  }
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  return resposta.json();
}

function mostraErros(formulario, erros) {
  const caixa = formulario.parentElement.querySelector(".erro");
  caixa.textContent = erros.join("\n");
  caixa.classList.add("visivel");
}

for (const formulario of document.querySelectorAll("form")) {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const aba = formulario.parentElement.id;
    const resposta = await envia(formulario, aba);
    if (!resposta.ok) {
      mostraErros(formulario, resposta.erros);
      return;
    }
    document.getElementById("oficio").textContent = resposta.oficio;
    for (const secao of document.querySelectorAll(".corpo, .abas")) secao.hidden = true;
    document.getElementById("confirmacao").hidden = false;
  });
}

// Abas
document.querySelectorAll(".aba-navegacao").forEach(function (botao, indice) {
  botao.addEventListener("click", function () {
    document.querySelectorAll(".aba-navegacao").forEach(function (b) {
      b.classList.remove("ativa");
      b.setAttribute("aria-selected", "false");
    });
    botao.classList.add("ativa");
    botao.setAttribute("aria-selected", "true");
    document.querySelectorAll("section.aba").forEach(function (secao) {
      secao.hidden = true;
    });
    document.getElementById(botao.textContent).hidden = false;
  });
});
