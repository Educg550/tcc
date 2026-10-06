"use strict";

const MASCARAS = {
  moeda(valor) {
    const d = valor.replace(/[^0-9]/g, "").slice(0, 11);
    if (!d) return "";
    const centavos = parseInt(d, 10);
    const inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + inteiro + "," + String(centavos % 100).padStart(2, "0");
  },
  cpf(valor) {
    const d = valor.replace(/[^0-9]/g, "").slice(0, 11);
    let r = d;
    if (d.length > 3) r = d.slice(0, 3) + "." + d.slice(3);
    if (d.length > 6) r = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 9) r = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    return r;
  },
  cep(valor) {
    const d = valor.replace(/[^0-9]/g, "").slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data(valor) {
    const d = valor.replace(/[^0-9]/g, "").slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }
};

for (const campo of document.querySelectorAll("[data-mascara]")) {
  const aplicar = () => { campo.value = MASCARAS[campo.dataset.mascara](campo.value); };
  campo.addEventListener("input", aplicar);
  campo.addEventListener("blur", aplicar);
}

const abas = Array.from(document.querySelectorAll(".aba"));
for (const aba of abas) {
  aba.addEventListener("click", () => {
    for (const outra of abas) {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", ativa ? "true" : "false");
      document.getElementById(outra.dataset.painel).hidden = !ativa;
    }
  });
}

for (const form of document.querySelectorAll("form.painel")) {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = {};
    for (const campo of form.querySelectorAll("[name]")) {
      dados[campo.name] = campo.value;
    }
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ perfil: form.dataset.perfil, dados: dados })
    });
    const resultado = await resposta.();
    if (resultado.ok) {
      document.getElementById("texto-oficio").textContent = resultado.oficio;
      document.getElementById("vis-formulario").hidden = true;
      document.getElementById("vis-confirmacao").hidden = false;
      window.scrollTo(0, 0);
    } else {
      const caixa = form.querySelector(".erros");
      caixa.replaceChildren(...resultado.erros.map((msg) => {
        const p = document.createElement("p");
        p.textContent = msg;
        return p;
      }));
      caixa.hidden = false;
    }
  });
}
