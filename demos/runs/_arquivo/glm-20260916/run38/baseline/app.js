const FORMATADORES = {
  moeda(texto) {
    const digitos = texto.replace(/\D/g, "").replace(/^0+(?=\d)/, "");
    if (!digitos) return "";
    const reais = Math.floor(Number(digitos) / 100).toString();
    const centavos = (Number(digitos) % 100).toString().padStart(2, "0");
    return `R$ ${reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${centavos}`;
  },
  cpf(texto) {
    const d = texto.replace(/\D/g, "").slice(0, 11);
    let formatado = d.slice(0, 3);
    if (d.length > 3) formatado += "." + d.slice(3, 6);
    if (d.length > 6) formatado += "." + d.slice(6, 9);
    if (d.length > 9) formatado += "-" + d.slice(9);
    return formatado;
  },
  cep(texto) {
    const d = texto.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  data(texto) {
    const d = texto.replace(/\D/g, "").slice(0, 8);
    let formatado = d.slice(0, 2);
    if (d.length > 2) formatado += "/" + d.slice(2, 4);
    if (d.length > 4) formatado += "/" + d.slice(4, 8);
    return formatado;
  },
};

for (const campo of document.querySelectorAll("[data-formato]")) {
  const formatar = FORMATADORES[campo.dataset.formato];
  const aplicar = () => { campo.value = formatar(campo.value); };
  campo.addEventListener("input", aplicar);
  campo.addEventListener("blur", aplicar);
}

for (const aba of document.querySelectorAll(".aba")) {
  aba.addEventListener("click", () => {
    for (const outra of document.querySelectorAll(".aba")) {
      outra.classList.toggle("ativa", outra === aba);
    }
    for (const painel of document.querySelectorAll(".painel")) {
      painel.hidden = painel.dataset.perfil !== aba.dataset.perfil;
    }
  });
}

for (const form of document.querySelectorAll("form.painel")) {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const campos = Object.fromEntries(new FormData(form).entries());
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ perfil: form.dataset.perfil, campos }),
    });
    const dados = await resposta.();
    const caixa = form.querySelector(".erros");
    if (dados.erros) {
      caixa.textContent = dados.erros.join("\n");
      caixa.hidden = false;
      caixa.scrollIntoView({ block: "nearest" });
      return;
    }
    document.getElementById("oficio").textContent = dados.oficio;
    document.getElementById("formularios").hidden = true;
    document.getElementById("confirmacao").hidden = false;
  });
}
