"use strict";

function soDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

function formataValor(bruto) {
  const digitos = soDigitos(bruto).slice(0, 15);
  if (!digitos) {
    return "";
  }
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100).toLocaleString("pt-BR");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function formataCpf(bruto) {
  const d = soDigitos(bruto).slice(0, 11);
  let texto = d.slice(0, 3);
  if (d.length > 3) {
    texto += "." + d.slice(3, 6);
  }
  if (d.length > 6) {
    texto += "." + d.slice(6, 9);
  }
  if (d.length > 9) {
    texto += "-" + d.slice(9);
  }
  return texto;
}

function formataCep(bruto) {
  const d = soDigitos(bruto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formataData(bruto) {
  const d = soDigitos(bruto).slice(0, 8);
  if (d.length <= 2) {
    return d;
  }
  if (d.length <= 4) {
    return d.slice(0, 2) + "/" + d.slice(2);
  }
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const FORMATO = {
  "VALOR SOLICITADO (R$)": formataValor,
  "CPF (SEPARADOS POR PONTOS E TRAÇO)": formataCpf,
  "CEP": formataCep,
  "DATA DE NASCIMENTO": formataData,
};

const abas = Array.from(document.querySelectorAll(".aba"));
const formularios = Array.from(document.querySelectorAll(".formulario"));
const pedido = document.getElementById("pedido");
const confirmacao = document.getElementById("confirmacao");
const oficio = document.getElementById("oficio");

function mostraAba(tipo) {
  abas.forEach(function (aba) {
    aba.classList.toggle("ativa", aba.dataset.aba === tipo);
  });
  formularios.forEach(function (formulario) {
    formulario.classList.toggle("ativa", formulario.dataset.tipo === tipo);
  });
}

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    mostraAba(aba.dataset.aba);
  });
});

formularios.forEach(function (formulario) {
  formulario.querySelectorAll("input").forEach(function (campo) {
    const formata = FORMATO[campo.name];
    if (!formata) {
      return;
    }
    const aoDigitar = function () {
      campo.value = formata(campo.value);
    };
    campo.addEventListener("input", aoDigitar);
    campo.addEventListener("blur", aoDigitar);
  });

  formulario.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const campos = {};
    new FormData(formulario).forEach(function (valor, chave) {
      campos[chave] = valor;
    });
    Object.keys(FORMATO).forEach(function (chave) {
      campos[chave] = soDigitos(campos[chave]);
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tipo: formulario.dataset.tipo, campos: campos }),
    });
    const corpo = await resposta.json();
    const erros = formulario.querySelector(".erros");
    if (corpo.erros.length) {
      erros.hidden = false;
      erros.replaceChildren(
        ...corpo.erros.map(function (mensagem) {
          const linha = document.createElement("p");
          linha.textContent = mensagem;
          return linha;
        })
      );
      return;
    }
    erros.hidden = true;
    oficio.textContent = corpo.oficio;
    pedido.hidden = true;
    confirmacao.hidden = false;
  });
});
