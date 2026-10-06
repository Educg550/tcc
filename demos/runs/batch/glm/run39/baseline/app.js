// Abas
const abas = [
  { botao: document.getElementById("aba-alunos"), painel: document.getElementById("form-alunos") },
  { botao: document.getElementById("aba-docentes"), painel: document.getElementById("form-docentes") },
];

for (const { botao, painel } of abas) {
  botao.addEventListener("click", () => {
    for (const outra of abas) {
      outra.botao.classList.toggle("ativa", outra.botao === botao);
      outra.botao.setAttribute("aria-selected", String(outra.botao === botao));
      outra.painel.classList.toggle("visivel", outra.painel === painel);
    }
  });
}

// Formatação enquanto se digita
const digitos = (texto) => texto.replace(/\D/g, "");

function formatarMoeda(texto) {
  const n = digitos(texto);
  if (!n) return "";
  const centavos = n.slice(-2).padStart(2, "0");
  const reais = n.slice(0, -2) || "0";
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
}

const formatadores = {
  moeda: (d) => formatarMoeda(d),
  cpf: (d) => (d.length > 9 ? d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9, 11) : d.replace(/(\d{3})(?=\d)/g, "$1.").replace(/(\d{3})\.(\d{3})(?=\d)/, "$1.$2")),
  cep: (d) => (d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5, 8) : d),
  data: (d) => (d.length > 4 ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4, 8) : d.length > 2 ? d.slice(0, 2) + "/" + d.slice(2, 4) : d),
};

const limites = { moeda: 12, cpf: 11, cep: 8, data: 8 };

for (const campo of document.querySelectorAll(".moeda, .cpf, .cep, .data")) {
  const tipo = [...campo.classList].find((c) => c in formatadores);
  campo.addEventListener("input", () => {
    campo.value = formatadores[tipo](digitos(campo.value).slice(0, limites[tipo]));
  });
}

// Envio
const app = document.getElementById("app");
const confirmacao = document.getElementById("confirmacao");

async function enviar(form, errosDiv) {
  const dados = Object.fromEntries(new FormData(form));
  dados.valor_centavos = Number(digitos(dados.valor));
  dados.valor = undefined;
  const corpo = {
    perfil: form.dataset.perfil,
    nome: dados.nome,
    nusp: dados.nusp,
    programa: dados.programa,
    nivel: dados.nivel || "",
    tipo_auxilio: dados.tipo_auxilio || "",
    email: dados.email,
    evento_nome: dados.evento_nome,
    evento_periodo: dados.evento_periodo,
    evento_cidade: dados.evento_cidade,
    evento_estado: dados.evento_estado,
    evento_pais: dados.evento_pais,
    evento_link: dados.evento_link || "",
    valor_centavos: dados.valor_centavos,
    detalhamento: dados.detalhamento,
    apresentacao: dados.apresentacao,
    endereco: {
      nascimento: dados.nascimento,
      logradouro: dados.logradouro,
      numero: dados.numero,
      complemento: dados.complemento || "",
      bairro: dados.bairro,
      cep: dados.cep,
      cidade: dados.cidade,
      estado: dados.estado,
    },
    pagamento: {
      cpf: dados.cpf,
      rg: dados.rg,
      banco: dados.banco,
      agencia: dados.agencia,
      conta: dados.conta,
    },
  };

  const resposta = await fetch("/api/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  const json = await resposta.json();

  errosDiv.innerHTML = "";
  if (!json.ok) {
    for (const msg of json.erros) {
      const p = document.createElement("p");
      p.textContent = msg;
      errosDiv.appendChild(p);
    }
    errosDiv.hidden = false;
    return;
  }

  app.hidden = true;
  document.getElementById("oficio").textContent = json.oficio;
  confirmacao.hidden = false;
}

for (const form of document.querySelectorAll("form")) {
  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviar(form, form.parentElement.querySelector(".erros"));
  });
}
