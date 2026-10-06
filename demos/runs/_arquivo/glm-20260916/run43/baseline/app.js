"use strict";

const formatadores = {
  moeda(el) {
    const d = el.value.replace(/\D/g, "");
    if (!d) {
      el.value = "";
      return;
    }
    const centavos = d.slice(-2).padStart(2, "0");
    const reais = (d.slice(0, -2) || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    el.value = "R$ " + reais + "," + centavos;
  },
  cpf(el) {
    const d = el.value.replace(/\D/g, "").slice(0, 11);
    let v = d.slice(0, 3);
    if (d.length > 3) v += "." + d.slice(3, 6);
    if (d.length > 6) v += "." + d.slice(6, 9);
    if (d.length > 9) v += "-" + d.slice(9, 11);
    el.value = v;
  },
  cep(el) {
    const d = el.value.replace(/\D/g, "").slice(0, 8);
    let v = d.slice(0, 5);
    if (d.length > 5) v += "-" + d.slice(5, 8);
    el.value = v;
  },
  data(el) {
    const d = el.value.replace(/\D/g, "").slice(0, 8);
    let v = d.slice(0, 2);
    if (d.length > 2) v += "/" + d.slice(2, 4);
    if (d.length > 4) v += "/" + d.slice(4, 8);
    el.value = v;
  }
};

document.querySelectorAll("[data-formato]").forEach((el) => {
  el.addEventListener("blur", () => formatadores[el.dataset.formato](el));
});

const abas = document.querySelectorAll(".aba");
const formularios = document.querySelectorAll(".formulario");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((a) => a.classList.toggle("ativa", a === aba));
    formularios.forEach((f) => {
      f.hidden = f.id !== aba.dataset.alvo;
    });
  });
});

function mostrarErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.replaceChildren(
    ...erros.map((mensagem) => {
      const item = document.createElement("div");
      item.textContent = mensagem;
      return item;
    })
  );
  caixa.hidden = false;
}

function mostrarConfirmacao(oficio) {
  document.querySelector(".abas").hidden = true;
  formularios.forEach((f) => {
    f.hidden = true;
  });
  document.querySelector(".oficio").textContent = oficio;
  document.getElementById("confirmacao").hidden = false;
}

formularios.forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { tipo: form.dataset.tipo };
    new FormData(form).forEach((valor, campo) => {
      dados[campo] = valor;
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    const corpo = await resposta.();
    if (corpo.ok) {
      mostrarConfirmacao(corpo.oficio);
    } else {
      mostrarErros(form, corpo.erros);
    }
  });
});
