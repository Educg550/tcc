function apenasDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

function formatarMoeda(campo) {
  const digitos = apenasDigitos(campo.value);
  if (!digitos) {
    campo.value = "";
    return;
  }
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const centavosTexto = String(centavos % 100).padStart(2, "0");
  campo.value = "R$ " + reais + "," + centavosTexto;
}

function formatarCpf(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 11);
  campo.value = digitos
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d{1,2})$/, ".$1-$2");
}

function formatarCep(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 8);
  campo.value = digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 8);
  if (digitos.length > 4) {
    campo.value = digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
  } else if (digitos.length > 2) {
    campo.value = digitos.slice(0, 2) + "/" + digitos.slice(2);
  } else {
    campo.value = digitos;
  }
}

function prepararFormatadores() {
  document.querySelectorAll("[data-formatar]").forEach((campo) => {
    campo.addEventListener("blur", () => {
      const tipo = campo.dataset.formatar;
      if (tipo === "moeda") formatarMoeda(campo);
      if (tipo === "cpf") formatarCpf(campo);
      if (tipo === "cep") formatarCep(campo);
      if (tipo === "data") formatarData(campo);
    });
  });
}

function prepararAbas() {
  const abas = document.querySelectorAll(".aba");
  abas.forEach((aba) => {
    aba.addEventListener("click", () => {
      abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
      document.querySelectorAll(".painel").forEach((painel) => {
        painel.classList.toggle("oculto", painel.id !== "painel-" + aba.dataset.aba);
      });
    });
  });
}

function coletarDados(form, aba) {
  const dados = { aba: aba };
  form.querySelectorAll("[name]").forEach((campo) => {
    dados[campo.name] = campo.value.trim();
  });
  if (dados.valor_solicitado !== undefined) {
    dados.valor_solicitado = apenasDigitos(dados.valor_solicitado);
  }
  return dados;
}

async function enviarSolicitacao(evento, aba) {
  evento.preventDefault();
  const form = evento.target;
  const quadroDeErros = form.querySelector(".erros");
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/" },
    body: JSON.stringify(coletarDados(form, aba)),
  });
  const conteudo = await resposta.();
  if (conteudo.erros && conteudo.erros.length > 0) {
    quadroDeErros.replaceChildren(
      ...conteudo.erros.map((mensagem) => {
        const paragrafo = document.createElement("p");
        paragrafo.textContent = mensagem;
        return paragrafo;
      })
    );
    quadroDeErros.hidden = false;
    return;
  }
  document.getElementById("oficio").textContent = conteudo.oficio;
  document.getElementById("abas").classList.add("oculto");
  document.querySelectorAll(".painel").forEach((painel) => painel.classList.add("oculto"));
  document.getElementById("confirmacao").classList.remove("oculto");
  window.scrollTo(0, 0);
}

document.addEventListener("DOMContentLoaded", () => {
  prepararAbas();
  prepararFormatadores();
  document
    .getElementById("form-alunos")
    .addEventListener("submit", (evento) => enviarSolicitacao(evento, "alunos"));
  document
    .getElementById("form-docentes")
    .addEventListener("submit", (evento) => enviarSolicitacao(evento, "docentes"));
});
