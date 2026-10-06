"use strict";

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const digitos = soDigitos(texto) || "0";
  const centavos = digitos.slice(-2).padStart(2, "0");
  const inteiro = digitos.slice(0, -2).replace(/^0+(?=\d)/, "") || "0";
  const milhar = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + milhar + "," + centavos;
}

function formatarCpf(texto) {
  return soDigitos(texto)
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatarCep(texto) {
  return soDigitos(texto).slice(0, 8).replace(/(\d{5})(\d)/, "$1-$2");
}

function formatarData(texto) {
  return soDigitos(texto)
    .slice(0, 8)
    .replace(/(\d{2})(\d)/, "$1/$2")
    .replace(/(\d{2})(\d)/, "$1/$2");
}

const abas = document.querySelectorAll(".aba");
const visaoFormularios = document.getElementById("visao-formularios");
const confirmacao = document.getElementById("confirmacao");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      document.getElementById(outra.dataset.alvo).hidden = !ativa;
    });
    confirmacao.hidden = true;
    visaoFormularios.hidden = false;
  });
});

document.querySelectorAll("input[data-formato]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

function configurarEnvio(idFormulario, idErros, aba) {
  const formulario = document.getElementById(idFormulario);
  const areaErros = document.getElementById(idErros);
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { aba: aba };
    new FormData(formulario).forEach((valor, chave) => {
      dados[chave] = String(valor).trim();
    });
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.();
    if (corpo.erros) {
      areaErros.replaceChildren();
      corpo.erros.forEach((mensagem) => {
        const paragrafo = document.createElement("p");
        paragrafo.textContent = mensagem;
        areaErros.appendChild(paragrafo);
      });
      areaErros.hidden = false;
      window.scrollTo(0, 0);
      return;
    }
    areaErros.hidden = true;
    document.getElementById("oficio").textContent = corpo.oficio;
    visaoFormularios.hidden = true;
    confirmacao.hidden = false;
    window.scrollTo(0, 0);
  });
}

configurarEnvio("form-alunos", "erros-alunos", "alunos");
configurarEnvio("form-docentes", "erros-docentes", "docentes");
