"use strict";

const formularios = Array.from(document.querySelectorAll(".formulario"));

/* ---------- abas ---------- */

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    formularios.forEach(function (form) {
      form.classList.toggle("ativo", form.dataset.aba === aba.dataset.aba);
    });
  });
});

/* ---------- máscaras aplicadas ao sair do campo ---------- */

const mascaras = {
  valor: function (valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 15);
    if (!digitos) return "";
    const numero = parseInt(digitos, 10) / 100;
    return "R$ " + numero.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  },
  cpf: function (valor) {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  },
  cep: function (valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data: function (valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }
};

document.querySelectorAll("[data-mask]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = mascaras[campo.dataset.mask](campo.value);
  });
});

/* ---------- envio ---------- */

function mostrarOficio(texto) {
  document.querySelector(".abas").hidden = true;
  formularios.forEach(function (form) {
    form.hidden = true;
  });
  document.getElementById("oficio").textContent = texto;
  document.getElementById("confirmacao").hidden = false;
}

formularios.forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    const dados = { aba: form.dataset.aba };
    form.querySelectorAll("[name]").forEach(function (campo) {
      dados[campo.name] = campo.value;
    });

    const resposta = await fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.json();

    const erros = form.querySelector(".erros");
    if (resultado.erros) {
      erros.textContent = resultado.erros.join("\n");
      erros.hidden = false;
      return;
    }

    erros.hidden = true;
    erros.textContent = "";
    mostrarOficio(resultado.oficio);
  });
});
