"use strict";

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(texto) {
  const centavos = digitos(texto);
  if (!centavos) {
    return "";
  }
  const inteiro = String(Math.floor(Number(centavos) / 100));
  const resto = String(Number(centavos) % 100).padStart(2, "0");
  return "R$ " + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + resto;
}

function formatarCpf(texto) {
  const num = digitos(texto).slice(0, 11);
  if (num.length > 9) {
    return num.slice(0, 3) + "." + num.slice(3, 6) + "." + num.slice(6, 9) + "-" + num.slice(9);
  }
  if (num.length > 6) {
    return num.slice(0, 3) + "." + num.slice(3, 6) + "." + num.slice(6);
  }
  if (num.length > 3) {
    return num.slice(0, 3) + "." + num.slice(3);
  }
  return num;
}

function formatarCep(texto) {
  const num = digitos(texto).slice(0, 8);
  if (num.length <= 5) {
    return num;
  }
  return num.slice(0, 5) + "-" + num.slice(5);
}

function formatarData(texto) {
  const num = digitos(texto).slice(0, 8);
  if (num.length <= 2) {
    return num;
  }
  if (num.length <= 4) {
    return num.slice(0, 2) + "/" + num.slice(2);
  }
  return num.slice(0, 2) + "/" + num.slice(2, 4) + "/" + num.slice(4);
}

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

document.querySelectorAll("input[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    const formatar = FORMATADORES[campo.dataset.formato];
    if (formatar) {
      campo.value = formatar(campo.value);
    }
  });
});

const abas = Array.from(document.querySelectorAll(".aba"));

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      document.getElementById(outra.dataset.alvo).hidden = !ativa;
    });
  });
});

document.querySelectorAll(".formulario").forEach(function (formulario) {
  formulario.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const resposta = await fetch("/solicitar", {
      method: "POST",
      body: new FormData(formulario),
    });
    const dados = await resposta.();
    const areaDeErros = formulario.querySelector(".erros");
    if (dados.oficio) {
      areaDeErros.hidden = true;
      document.querySelector(".abas").hidden = true;
      document.querySelectorAll(".formulario").forEach(function (outra) {
        outra.hidden = true;
      });
      document.getElementById("oficio").textContent = dados.oficio;
      document.getElementById("confirmacao").hidden = false;
      window.scrollTo(0, 0);
      return;
    }
    areaDeErros.innerHTML = "";
    (dados.erros || []).forEach(function (mensagem) {
      const paragrafo = document.createElement("p");
      paragrafo.textContent = mensagem;
      areaDeErros.appendChild(paragrafo);
    });
    areaDeErros.hidden = false;
  });
});
