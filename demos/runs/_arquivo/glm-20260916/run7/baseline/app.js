"use strict";

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) {
    return "";
  }
  const comCentavos = digitos.padStart(3, "0");
  const reais = String(parseInt(comCentavos.slice(0, -2), 10));
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + comCentavos.slice(-2);
}

function formatarCpf(texto) {
  const digitos = soDigitos(texto).slice(0, 11);
  let formatado = digitos.slice(0, 3);
  if (digitos.length > 3) formatado += "." + digitos.slice(3, 6);
  if (digitos.length > 6) formatado += "." + digitos.slice(6, 9);
  if (digitos.length > 9) formatado += "-" + digitos.slice(9, 11);
  return formatado;
}

function formatarCep(texto) {
  const digitos = soDigitos(texto).slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(texto) {
  const digitos = soDigitos(texto).slice(0, 8);
  let formatado = digitos.slice(0, 2);
  if (digitos.length > 2) formatado += "/" + digitos.slice(2, 4);
  if (digitos.length > 4) formatado += "/" + digitos.slice(4, 8);
  return formatado;
}

const MASCARAS = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

document.querySelectorAll("input[data-mascara]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = MASCARAS[campo.dataset.mascara](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.setAttribute("aria-selected", String(outra === aba)));
    document.querySelectorAll(".painel").forEach((painel) => {
      painel.hidden = painel.id !== aba.dataset.painel;
    });
  });
});

document.querySelectorAll("form.solicitacao").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const dados = {};
    form.querySelectorAll("[name]").forEach((campo) => {
      dados[campo.name] = campo.value.trim();
    });
    if ("VALOR SOLICITADO (R$)" in dados) {
      dados["VALOR SOLICITADO (R$)"] = soDigitos(dados["VALOR SOLICITADO (R$)"]);
    }
    if ("CPF (SEPARADOS POR PONTOS E TRAÇO)" in dados) {
      dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = formatarCpf(dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"]);
    }
    if ("CEP" in dados) {
      dados["CEP"] = formatarCep(dados["CEP"]);
    }
    if ("DATA DE NASCIMENTO" in dados) {
      dados["DATA DE NASCIMENTO"] = formatarData(dados["DATA DE NASCIMENTO"]);
    }

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ perfil: form.dataset.perfil, dados: dados }),
    });
    const conteudo = await resposta.();

    const erros = form.querySelector(".erros");
    if (conteudo.erros && conteudo.erros.length > 0) {
      erros.replaceChildren(
        ...conteudo.erros.map((mensagem) => {
          const paragrafo = document.createElement("p");
          paragrafo.textContent = mensagem;
          return paragrafo;
        })
      );
      erros.hidden = false;
    } else if (conteudo.oficio) {
      document.querySelector(".abas").hidden = true;
      document.querySelectorAll(".painel").forEach((painel) => {
        painel.hidden = true;
      });
      const confirmacao = document.getElementById("confirmacao");
      confirmacao.querySelector(".oficio").textContent = conteudo.oficio;
      confirmacao.hidden = false;
      window.scrollTo(0, 0);
    }
  });
});
