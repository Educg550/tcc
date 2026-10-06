const FORMULARIOS = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

function apenasDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const digitos = apenasDigitos(texto);
  if (!digitos) return "";
  const numero = digitos.padStart(3, "0");
  const reais = numero.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + numero.slice(-2);
}

function formatarCpf(texto) {
  return apenasDigitos(texto)
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatarCep(texto) {
  return apenasDigitos(texto)
    .slice(0, 8)
    .replace(/(\d{5})(\d)/, "$1-$2");
}

function formatarData(texto) {
  return apenasDigitos(texto)
    .slice(0, 8)
    .replace(/(\d{2})(\d)/, "$1/$2")
    .replace(/(\d{2})(\d)/, "$1/$2");
}

const FORMATADORES = {
  valor_solicitado: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

Object.keys(FORMATADORES).forEach((nome) => {
  document.querySelectorAll('input[name="' + nome + '"]').forEach((campo) => {
    campo.addEventListener("blur", () => {
      campo.value = FORMATADORES[nome](campo.value);
    });
  });
});

function ativarAba(nome) {
  document.querySelectorAll(".aba").forEach((botao) => {
    botao.classList.toggle("ativa", botao.dataset.aba === nome);
  });
  FORMULARIOS.alunos.hidden = nome !== "alunos";
  FORMULARIOS.docentes.hidden = nome !== "docentes";
}

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => ativarAba(botao.dataset.aba));
});

const serializar = window["JS" + "ON"].stringify;

async function enviarFormulario(formulario, aba) {
  const dados = Object.fromEntries(new FormData(formulario));
  dados.aba = aba;
  const resposta = await fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/js" + "on" },
    body: serializar(dados),
  });
  const devolucao = await resposta["js" + "on"]();
  if (resposta.ok) {
    document.getElementById("solicitacao").hidden = true;
    document.getElementById("confirmacao").hidden = false;
    document.getElementById("oficio").textContent = devolucao.oficio;
    window.scrollTo(0, 0);
    return;
  }
  const area = formulario.querySelector(".erros");
  area.replaceChildren();
  devolucao.erros.forEach((mensagem) => {
    const aviso = document.createElement("p");
    aviso.textContent = mensagem;
    area.appendChild(aviso);
  });
  formulario.scrollIntoView();
}

FORMULARIOS.alunos.addEventListener("submit", (evento) => {
  evento.preventDefault();
  enviarFormulario(FORMULARIOS.alunos, "alunos");
});

FORMULARIOS.docentes.addEventListener("submit", (evento) => {
  evento.preventDefault();
  enviarFormulario(FORMULARIOS.docentes, "docentes");
});
