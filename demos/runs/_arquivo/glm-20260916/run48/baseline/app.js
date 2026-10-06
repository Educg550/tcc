const formatadores = {
  moeda(valor) {
    const d = valor.replace(/\D/g, "");
    if (!d) return "";
    const p = d.padStart(3, "0");
    const inteiro = p.slice(0, -2).replace(/^0+(?=\d)/, "");
    return "R$ " + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + p.slice(-2);
  },
  cpf(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    let r = d.slice(0, 3);
    if (d.length > 3) r += "." + d.slice(3, 6);
    if (d.length > 6) r += "." + d.slice(6, 9);
    if (d.length > 9) r += "-" + d.slice(9, 11);
    return r;
  },
  cep(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    let r = d.slice(0, 2);
    if (d.length > 2) r += "/" + d.slice(2, 4);
    if (d.length > 4) r += "/" + d.slice(4, 8);
    return r;
  }
};

document.querySelectorAll("[data-formato]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = formatadores[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    document.querySelectorAll(".formulario").forEach((painel) => {
      painel.hidden = painel.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(form));
    dados.tipo = form.dataset.tipo;
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    const saida = await resposta.();
    if (saida.oficio) {
      document.getElementById("painel-formularios").hidden = true;
      document.getElementById("oficio").textContent = saida.oficio;
      document.getElementById("confirmacao").hidden = false;
      window.scrollTo(0, 0);
    } else {
      const caixa = form.querySelector(".erros");
      caixa.replaceChildren(
        ...saida.erros.map((mensagem) => {
          const p = document.createElement("p");
          p.textContent = mensagem;
          return p;
        })
      );
      caixa.hidden = false;
    }
  });
});
