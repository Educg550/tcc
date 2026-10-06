"use strict";

function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarValor(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) return "";
  const centavos = digitos.slice(-2).padStart(2, "0");
  let reais = digitos.slice(0, -2).replace(/^0+(?=\d)/, "");
  if (!reais) reais = "0";
  const milhar = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + milhar + "," + centavos;
}

function formatarCPF(valor) {
  const digitos = soDigitos(valor).slice(0, 11);
  let formatado = digitos.slice(0, 3);
  if (digitos.length > 3) formatado += "." + digitos.slice(3, 6);
  if (digitos.length > 6) formatado += "." + digitos.slice(6, 9);
  if (digitos.length > 9) formatado += "-" + digitos.slice(9);
  return formatado;
}

function formatarCEP(valor) {
  const digitos = soDigitos(valor).slice(0, 8);
  let formatado = digitos.slice(0, 5);
  if (digitos.length > 5) formatado += "-" + digitos.slice(5);
  return formatado;
}

function formatarData(valor) {
  const digitos = soDigitos(valor).slice(0, 8);
  let formatado = digitos.slice(0, 2);
  if (digitos.length > 2) formatado += "/" + digitos.slice(2, 4);
  if (digitos.length > 4) formatado += "/" + digitos.slice(4);
  return formatado;
}

const MASCARAS = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData,
};

document.querySelectorAll("input[name]").forEach(function (campo) {
  const formatar = MASCARAS[campo.name];
  if (formatar) {
    campo.addEventListener("blur", function () {
      campo.value = formatar(campo.value);
    });
  }
});

const FORMULARIOS = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    for (const chave of Object.keys(FORMULARIOS)) {
      FORMULARIOS[chave].hidden = chave !== aba.dataset.aba;
    }
  });
});

function dadosDoFormulario(form) {
  const campos = {};
  for (const controle of form.elements) {
    if (!controle.name) continue;
    campos[controle.name] = controle.name === "valor" ? soDigitos(controle.value) : controle.value;
  }
  return campos;
}

async function enviarSolicitacao(form, aba) {
  const aviso = form.querySelector(".erros");
  const resposta = await fetch("/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ aba: aba, campos: dadosDoFormulario(form) }),
  });
  const dados = await resposta.json();
  if (!dados.ok) {
    aviso.replaceChildren(...dados.erros.map(function (mensagem) {
      const linha = document.createElement("p");
      linha.textContent = mensagem;
      return linha;
    }));
    aviso.hidden = false;
    return;
  }
  document.getElementById("oficio").textContent = dados.oficio;
  document.getElementById("formulario").hidden = true;
  document.getElementById("confirmacao").hidden = false;
  window.scrollTo(0, 0);
}

FORMULARIOS.alunos.addEventListener("submit", function (evento) {
  evento.preventDefault();
  enviarSolicitacao(evento.target, "alunos");
});

FORMULARIOS.docentes.addEventListener("submit", function (evento) {
  evento.preventDefault();
  enviarSolicitacao(evento.target, "docentes");
});
