const formatadores = {
  valor(texto) {
    const digitos = texto.replace(/\D/g, "");
    if (!digitos) return "";
    const centavos = Number(digitos);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `R$ ${reais},${String(centavos % 100).padStart(2, "0")}`;
  },
  cpf(texto) {
    const digitos = texto.replace(/\D/g, "").slice(0, 11);
    if (digitos.length <= 3) return digitos;
    if (digitos.length <= 6) return `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
    if (digitos.length <= 9) return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
    return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9)}`;
  },
  cep(texto) {
    const digitos = texto.replace(/\D/g, "").slice(0, 8);
    return digitos.length <= 5 ? digitos : `${digitos.slice(0, 5)}-${digitos.slice(5)}`;
  },
  data(texto) {
    const digitos = texto.replace(/\D/g, "").slice(0, 8);
    return [digitos.slice(0, 2), digitos.slice(2, 4), digitos.slice(4, 8)].filter(Boolean).join("/");
  },
};

document.querySelectorAll("[data-format]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = formatadores[campo.dataset.format](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
const paineis = document.querySelectorAll(".painel");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    paineis.forEach((painel) => painel.classList.toggle("ativo", painel.dataset.aba === aba.dataset.aba));
  });
});

function mostrarErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.textContent = "";
  erros.forEach((mensagem) => {
    const linha = document.createElement("p");
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
  caixa.hidden = erros.length === 0;
}

paineis.forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    form.querySelectorAll("[data-format]").forEach((campo) => {
      campo.value = formatadores[campo.dataset.format](campo.value);
    });

    const dados = { aba: form.dataset.aba };
    form.querySelectorAll("[name]").forEach((campo) => {
      dados[campo.name] = campo.value.trim();
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    if (resultado.erros.length > 0) {
      mostrarErros(form, resultado.erros);
      return;
    }

    document.querySelector(".abas").hidden = true;
    document.querySelector("main").hidden = true;
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
});
