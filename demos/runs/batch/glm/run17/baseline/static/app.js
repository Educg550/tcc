"use strict";

// ------------------------------------------------------------------ abas

const abas = document.querySelectorAll(".aba");
const paineis = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

function ativarAba(nome) {
  abas.forEach((aba) => aba.classList.toggle("ativa", aba.dataset.aba === nome));
  for (const [tipo, painel] of Object.entries(paineis)) {
    painel.hidden = tipo !== nome;
  }
}

abas.forEach((aba) => aba.addEventListener("click", () => ativarAba(aba.dataset.aba)));

// --------------------------------------------------- formatação ao sair do campo

function formatarMoeda(digitos) {
  const centavos = parseInt(digitos || "0", 10);
  const texto = (centavos / 100).toFixed(2).replace(".", ",");
  const [inteiro, decimos] = texto.split(",");
  const separado = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + separado + "," + decimos;
}

function formatarCPF(digitos) {
  return digitos.replace(/\D/g, "").slice(0, 11)
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
}

function formatarCEP(digitos) {
  const d = digitos.replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(digitos) {
  const d = digitos.replace(/\D/g, "").slice(0, 8);
  if (d.length <= 4) return d;
  if (d.length <= 6) return d.slice(0, 2) + "/" + d.slice(2);
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const formatadores = {
  "formatar-moeda": formatarMoeda,
  "formatar-cpf": formatarCPF,
  "formatar-cep": formatarCEP,
  "formatar-data": formatarData,
};

for (const [classe, formatar] of Object.entries(formatadores)) {
  document.querySelectorAll("." + classe).forEach((campo) => {
    campo.addEventListener("blur", () => {
      campo.value = formatar(campo.value);
    });
  });
}

// ------------------------------------------------------------------ envio

const confirmacao = document.getElementById("confirmacao");
const oficio = document.getElementById("oficio");
const botaoNova = document.getElementById("nova-solicitacao");

function mostrarErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.replaceChildren(
    ...erros.map((mensagem) => {
      const p = document.createElement("p");
      p.textContent = mensagem;
      return p;
    }),
  );
}

function coletarDados(form, tipo) {
  const dados = Object.fromEntries(new FormData(form).entries());
  dados.complemento = dados.complemento || "";
  dados.link_do_evento = dados.link_do_evento || "";
  if (tipo === "docentes") {
    dados.nivel = "";
    dados.tipo_de_auxilio = "";
  } else {
    dados.nivel = dados.nivel || "";
    dados.tipo_de_auxilio = dados.tipo_de_auxilio || "";
  }
  return {
    nome: dados.nome,
    numero_usp: dados.numero_usp,
    programa: dados.programa,
    nivel: dados.nivel,
    tipo_de_auxilio: dados.tipo_de_auxilio,
    email: dados.email,
    nome_do_evento: dados.nome_do_evento,
    periodo_do_evento: dados.periodo_do_evento,
    cidade_do_evento: dados.cidade_do_evento,
    estado_do_evento: dados.estado_do_evento,
    pais_do_evento: dados.pais_do_evento,
    link_do_evento: dados.link_do_evento,
    valor_solicitado: dados.valor_solicitado,
    detalhamento: dados.detalhamento,
    apresentacao: dados.apresentacao,
    data_de_nascimento: dados.data_de_nascimento,
    endereco: {
      logradouro: dados.logradouro,
      numero: dados.numero,
      complemento: dados.complemento,
      bairro: dados.bairro,
      cep: dados.cep,
      cidade: dados.cidade,
      estado: dados.estado,
    },
    cpf: dados.cpf,
    rg: dados.rg,
    banco: dados.banco,
    agencia: dados.agencia,
    conta: dados.conta,
  };
}

for (const [tipo, form] of Object.entries(paineis)) {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletarDados(form, tipo)),
    });
    const resultado = await resposta.json();
    if (resultado.erros && resultado.erros.length > 0) {
      mostrarErros(form, resultado.erros);
      return;
    }
    mostrarErros(form, []);
    oficio.textContent = resultado.oficio;
    document.querySelector(".abas").hidden = true;
    for (const painel of Object.values(paineis)) painel.hidden = true;
    confirmacao.hidden = false;
    confirmacao.scrollIntoView();
  });
}

botaoNova.addEventListener("click", () => {
  confirmacao.hidden = true;
  document.querySelector(".abas").hidden = false;
  const abaAtiva = document.querySelector(".aba.ativa").dataset.aba;
  paineis[abaAtiva].hidden = false;
});
