"use strict";

function soDigitos(texto) {
  return (texto.match(/\d/g) || []).join("");
}

function formatarValor(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const resto = String(centavos % 100).padStart(2, "0");
  const milhar = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + milhar + "," + resto;
}

function formatarCPF(texto) {
  const digitos = soDigitos(texto);
  let resultado = digitos.slice(0, 3);
  if (digitos.length > 3) {
    resultado += "." + digitos.slice(3, 6);
  }
  if (digitos.length > 6) {
    resultado += "." + digitos.slice(6, 9);
  }
  if (digitos.length > 9) {
    resultado += "-" + digitos.slice(9, 11);
  }
  return resultado;
}

function formatarCEP(texto) {
  const digitos = soDigitos(texto);
  if (digitos.length <= 5) {
    return digitos;
  }
  return digitos.slice(0, 5) + "-" + digitos.slice(5, 8);
}

function formatarData(texto) {
  const digitos = soDigitos(texto);
  let resultado = digitos.slice(0, 2);
  if (digitos.length > 2) {
    resultado += "/" + digitos.slice(2, 4);
  }
  if (digitos.length > 4) {
    resultado += "/" + digitos.slice(4, 8);
  }
  return resultado;
}

const mascaras = {
  "mascara-valor": formatarValor,
  "mascara-cpf": formatarCPF,
  "mascara-cep": formatarCEP,
  "mascara-data": formatarData
};

Object.keys(mascaras).forEach(function (classe) {
  const formatar = mascaras[classe];
  document.querySelectorAll("." + classe).forEach(function (campo) {
    campo.addEventListener("input", function () {
      campo.value = formatar(campo.value);
    });
    campo.addEventListener("blur", function () {
      campo.value = formatar(campo.value);
    });
  });
});

const formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes")
};

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (botao) {
      botao.classList.toggle("ativa", botao === aba);
    });
    Object.keys(formularios).forEach(function (nome) {
      formularios[nome].hidden = nome !== aba.dataset.aba;
    });
  });
});

Object.keys(formularios).forEach(function (nome) {
  const form = formularios[nome];
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const campos = {};
    form.querySelectorAll("label").forEach(function (rotulo) {
      const campo = document.getElementById(rotulo.htmlFor);
      if (campo) {
        campos[rotulo.textContent.trim()] = campo.value;
      }
    });
    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: nome, campos: campos })
    });
    const resultado = await resposta.json();
    const caixa = form.querySelector(".erros");
    if (resultado.erros.length) {
      caixa.replaceChildren();
      resultado.erros.forEach(function (mensagem) {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      });
      caixa.hidden = false;
      return;
    }
    document.querySelector(".abas").hidden = true;
    formularios.alunos.hidden = true;
    formularios.docentes.hidden = true;
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
});
