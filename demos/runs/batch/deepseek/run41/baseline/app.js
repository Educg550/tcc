const MASCARAS = {
  moeda(valor) {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    const [inteiro, centavos] = (Number(digitos) / 100).toFixed(2).split(".");
    return "R$ " + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
  },
  cpf(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    let saida = d.slice(0, 3);
    if (d.length > 3) saida += "." + d.slice(3, 6);
    if (d.length > 6) saida += "." + d.slice(6, 9);
    if (d.length > 9) saida += "-" + d.slice(9);
    return saida;
  },
  cep(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    let saida = d.slice(0, 2);
    if (d.length > 2) saida += "/" + d.slice(2, 4);
    if (d.length > 4) saida += "/" + d.slice(4);
    return saida;
  },
};

function formatar(campo) {
  campo.value = MASCARAS[campo.dataset.mascara](campo.value);
}

document.querySelectorAll("[data-mascara]").forEach(campo => {
  campo.addEventListener("blur", () => formatar(campo));
});

document.querySelectorAll(".aba").forEach(botao => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach(b => {
      const ativa = b === botao;
      b.classList.toggle("ativa", ativa);
      b.setAttribute("aria-selected", ativa);
    });
    document.querySelectorAll(".painel").forEach(painel => {
      painel.hidden = painel.id !== "painel-" + botao.dataset.aba;
    });
  });
});

document.querySelectorAll(".formulario").forEach(formulario => {
  formulario.addEventListener("submit", async evento => {
    evento.preventDefault();
    formulario.querySelectorAll("[data-mascara]").forEach(formatar);

    const dados = { aba: formulario.dataset.aba };
    new FormData(formulario).forEach((valor, chave) => { dados[chave] = valor; });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    const erros = formulario.parentElement.querySelector(".erros");
    if (!resultado.valido) {
      erros.textContent = resultado.erros.join("\n");
      erros.hidden = false;
      return;
    }

    erros.hidden = true;
    document.getElementById("oficio").textContent = resultado.oficio;
    document.querySelector(".abas").hidden = true;
    document.querySelectorAll(".painel").forEach(painel => { painel.hidden = true; });
    document.getElementById("confirmacao").hidden = false;
  });
});
