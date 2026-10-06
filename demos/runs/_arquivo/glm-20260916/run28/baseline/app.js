"use strict";

function agruparMilhar(numero) {
  let resto = String(numero);
  let agrupado = "";
  while (resto.length > 3) {
    agrupado = "." + resto.slice(-3) + agrupado;
    resto = resto.slice(0, -3);
  }
  return resto + agrupado;
}

function formatarMoeda(digitos) {
  if (!digitos) {
    return "";
  }
  const centavos = Number(digitos);
  const reais = Math.floor(centavos / 100);
  const resto = String(centavos % 100).padStart(2, "0");
  return "R$ " + agruparMilhar(reais) + "," + resto;
}

function formatarCpf(digitos) {
  let formatado = digitos.slice(0, 3);
  if (digitos.length > 3) {
    formatado += "." + digitos.slice(3, 6);
  }
  if (digitos.length > 6) {
    formatado += "." + digitos.slice(6, 9);
  }
  if (digitos.length > 9) {
    formatado += "-" + digitos.slice(9, 11);
  }
  return formatado;
}

function formatarCep(digitos) {
  let formatado = digitos.slice(0, 5);
  if (digitos.length > 5) {
    formatado += "-" + digitos.slice(5, 8);
  }
  return formatado;
}

function formatarData(digitos) {
  let formatado = digitos.slice(0, 2);
  if (digitos.length > 2) {
    formatado += "/" + digitos.slice(2, 4);
  }
  if (digitos.length > 4) {
    formatado += "/" + digitos.slice(4, 8);
  }
  return formatado;
}

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function digitosDo(campo) {
  let digitos = campo.value.replace(/\D/g, "");
  const maximo = Number(campo.dataset.max || 0);
  if (maximo) {
    digitos = digitos.slice(0, maximo);
  }
  return digitos;
}

document.querySelectorAll("input[data-formato]").forEach(function (campo) {
  campo.addEventListener("input", function () {
    campo.value = digitosDo(campo);
  });
  campo.addEventListener("blur", function () {
    campo.value = FORMATADORES[campo.dataset.formato](digitosDo(campo));
  });
});

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (outra) {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    document.getElementById("painel-alunos").hidden = aba.id !== "aba-alunos";
    document.getElementById("painel-docentes").hidden = aba.id !== "aba-docentes";
  });
});

document.querySelectorAll("form.solicitacao").forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    form.querySelectorAll("input[data-formato]").forEach(function (campo) {
      campo.value = FORMATADORES[campo.dataset.formato](digitosDo(campo));
    });
    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach(function (valor, campo) {
      dados[campo] = valor;
    });
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    const caixa = form.querySelector(".erros");
    if (resultado.erros) {
      caixa.replaceChildren(
        ...resultado.erros.map(function (mensagem) {
          const paragrafo = document.createElement("p");
          paragrafo.textContent = mensagem;
          return paragrafo;
        })
      );
      caixa.hidden = false;
      caixa.scrollIntoView({ block: "nearest" });
    } else {
      document.getElementById("texto-oficio").textContent = resultado.oficio;
      document.querySelector(".abas").hidden = true;
      document.getElementById("painel-alunos").hidden = true;
      document.getElementById("painel-docentes").hidden = true;
      document.getElementById("confirmacao").hidden = false;
      window.scrollTo(0, 0);
    }
  });
});
