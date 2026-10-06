"use strict";

const abas = {
  alunos: document.getElementById("aba-alunos"),
  docentes: document.getElementById("aba-docentes"),
};

const paineis = {
  alunos: document.getElementById("painel-alunos"),
  docentes: document.getElementById("painel-docentes"),
};

function mostrarAba(nome) {
  for (const chave of Object.keys(abas)) {
    const ativa = chave === nome;
    abas[chave].classList.toggle("ativa", ativa);
    abas[chave].setAttribute("aria-selected", String(ativa));
    paineis[chave].hidden = !ativa;
  }
}

for (const [nome, aba] of Object.entries(abas)) {
  aba.addEventListener("click", () => mostrarAba(nome));
}

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) {
    return "";
  }
  const centavos = digitos.slice(-2).padStart(2, "0");
  const reais = digitos.slice(0, -2) || "0";
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
}

function formatarCPF(texto) {
  const digitos = soDigitos(texto).slice(0, 11);
  let saida = digitos.slice(0, 3);
  if (digitos.length > 3) {
    saida += "." + digitos.slice(3, 6);
  }
  if (digitos.length > 6) {
    saida += "." + digitos.slice(6, 9);
  }
  if (digitos.length > 9) {
    saida += "-" + digitos.slice(9, 11);
  }
  return saida;
}

function formatarCEP(texto) {
  const digitos = soDigitos(texto).slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(texto) {
  const digitos = soDigitos(texto).slice(0, 8);
  let saida = digitos.slice(0, 2);
  if (digitos.length > 2) {
    saida += "/" + digitos.slice(2, 4);
  }
  if (digitos.length > 4) {
    saida += "/" + digitos.slice(4);
  }
  return saida;
}

const mascaras = {
  moeda: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

for (const campo of document.querySelectorAll("[data-mascara]")) {
  campo.addEventListener("blur", () => {
    campo.value = mascaras[campo.dataset.mascara](campo.value);
  });
}

for (const formulario of document.querySelectorAll("form")) {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { formulario: formulario.dataset.formulario };
    for (const controle of formulario.querySelectorAll("input, select, textarea")) {
      dados[controle.name] = controle.value.trim();
    }
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    if (resultado.valido) {
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("conteudo").hidden = true;
      document.getElementById("confirmacao").hidden = false;
    } else {
      const caixa = formulario.querySelector(".erros");
      caixa.replaceChildren();
      for (const mensagem of resultado.erros) {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      }
      caixa.hidden = false;
    }
    window.scrollTo(0, 0);
  });
}
