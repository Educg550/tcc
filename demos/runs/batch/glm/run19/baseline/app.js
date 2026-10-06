// Abas ------------------------------------------------------------
const abas = document.querySelectorAll(".aba");
const paineis = {
  ALUNOS: document.getElementById("form-alunos"),
  DOCENTES: document.getElementById("form-docentes"),
};

for (const aba of abas) {
  aba.addEventListener("click", () => mostrarAba(aba.id.slice(4)));
}

function mostrarAba(nome) {
  for (const aba of abas) {
    const ativa = aba.id === "aba-" + nome;
    aba.classList.toggle("ativa", ativa);
    aba.setAttribute("aria-selected", String(ativa));
  }
  for (const chave in paineis) paineis[chave].hidden = chave !== nome;
}

// Formatação automática --------------------------------------------
function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarMoeda(valor) {
  const digitos = soDigitos(valor).slice(0, 15);
  if (!digitos) return "";
  const centavos = digitos.padStart(3, "0");
  const reais = centavos.slice(0, -2);
  const sep = reais.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");
  return "R$ " + sep + "," + centavos.slice(-2);
}

function formatarCPF(valor) {
  const d = soDigitos(valor).slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += "." + d.slice(3, 6);
  if (d.length > 6) saida += "." + d.slice(6, 9);
  if (d.length > 9) saida += "-" + d.slice(9);
  return saida;
}

function formatarCEP(valor) {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += "/" + d.slice(2, 4);
  if (d.length > 4) saida += "/" + d.slice(4);
  return saida;
}

const formatadores = {
  "data-moeda": formatarMoeda,
  "data-cpf": formatarCPF,
  "data-cep": formatarCEP,
  "data-data": formatarData,
};

for (const campo of document.querySelectorAll("[data-moeda],[data-cpf],[data-cep],[data-data]")) {
  const formatar = formatadores[
    campo.hasAttribute("data-moeda") ? "data-moeda" :
    campo.hasAttribute("data-cpf") ? "data-cpf" :
    campo.hasAttribute("data-cep") ? "data-cep" : "data-data"
  ];
  campo.addEventListener("blur", () => {
    campo.value = formatar(campo.value);
  });
}

// Envio ------------------------------------------------------------
const confirmacao = document.getElementById("confirmacao");
const oficio = document.getElementById("oficio");

for (const nome in paineis) {
  const form = paineis[nome];
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const erros = form.querySelector(".erros");
    erros.textContent = "";
    const dados = Object.fromEntries(new FormData(form));
    dados.destino = nome.toLowerCase();
    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.json();
    if (corpo.oficio) {
      document.getElementById("pagina").replaceChildren(confirmacao);
      confirmacao.hidden = false;
      oficio.textContent = corpo.oficio;
    } else {
      erros.textContent = corpo.erros.join("\n");
      erros.hidden = false;
    }
  });
}
