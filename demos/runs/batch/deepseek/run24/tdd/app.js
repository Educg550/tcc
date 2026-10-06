const mascaras = {
  moeda: (valor) => {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    return (Number(digitos) / 100).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  },
  cpf: (valor) => {
    const digitos = valor.replace(/\D/g, "").slice(0, 11);
    if (digitos.length !== 11) return valor;
    return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  },
  cep: (valor) => {
    const digitos = valor.replace(/\D/g, "").slice(0, 8);
    if (digitos.length !== 8) return valor;
    return digitos.replace(/(\d{5})(\d{3})/, "$1-$2");
  },
  data: (valor) => {
    const digitos = valor.replace(/\D/g, "").slice(0, 8);
    if (digitos.length !== 8) return valor;
    return digitos.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
  },
};

document.querySelectorAll("[data-mascara]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = mascaras[campo.dataset.mascara](campo.value.trim());
  });
});

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", String(ativa));
    });
    document.querySelectorAll(".formulario").forEach((formulario) => {
      formulario.classList.toggle("ativo", formulario.dataset.aba === aba.dataset.aba);
    });
  });
});

document.querySelectorAll(".formulario").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const resposta = await fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        aba: formulario.dataset.aba,
        campos: Object.fromEntries(new FormData(formulario).entries()),
      }),
    });
    const resultado = await resposta.json();
    const area = formulario.querySelector(".erros");
    area.replaceChildren(
      ...resultado.erros.map((mensagem) => {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        return linha;
      })
    );
    if (resultado.erros.length === 0) {
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("tela-formulario").classList.add("escondido");
      document.getElementById("tela-confirmacao").classList.remove("escondido");
    }
  });
});
