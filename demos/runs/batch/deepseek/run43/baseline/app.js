const MASCARAS = {
  valor(v) {
    const d = v.replace(/\D/g, "");
    if (!d) return "";
    const centavos = parseInt(d, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
  },
  cpf(v) {
    const d = v.replace(/\D/g, "").slice(0, 11);
    let out = d.slice(0, 3);
    if (d.length > 3) out += "." + d.slice(3, 6);
    if (d.length > 6) out += "." + d.slice(6, 9);
    if (d.length > 9) out += "-" + d.slice(9, 11);
    return out;
  },
  cep(v) {
    const d = v.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  nascimento(v) {
    const d = v.replace(/\D/g, "").slice(0, 8);
    let out = d.slice(0, 2);
    if (d.length > 2) out += "/" + d.slice(2, 4);
    if (d.length > 4) out += "/" + d.slice(4, 8);
    return out;
  },
};

const abas = document.querySelectorAll(".aba");
const formularios = document.querySelectorAll(".formulario");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", String(ativa));
    });
    formularios.forEach((form) => {
      form.hidden = form.dataset.aba !== aba.dataset.aba;
    });
  });
});

formularios.forEach((form) => {
  const formatados = form.querySelectorAll("[data-mask]");

  formatados.forEach((campo) => {
    campo.addEventListener("blur", () => {
      campo.value = MASCARAS[campo.dataset.mask](campo.value);
    });
  });

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    formatados.forEach((campo) => {
      campo.value = MASCARAS[campo.dataset.mask](campo.value);
    });

    const campos = {};
    form.querySelectorAll("[name]").forEach((campo) => {
      campos[campo.name] = campo.value.trim();
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: form.dataset.aba, campos: campos }),
    });
    const dados = await resposta.json();

    if (dados.oficio) {
      document.getElementById("app").hidden = true;
      document.getElementById("oficio").textContent = dados.oficio;
      document.getElementById("confirmacao").hidden = false;
    } else {
      form.querySelector(".erros").textContent = dados.erros.join("\n");
    }
  });
});
