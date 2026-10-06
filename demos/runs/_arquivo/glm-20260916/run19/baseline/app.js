const FORMATADORES = {
  valor(valor) {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    const centavos = digitos.slice(-2).padStart(2, "0");
    const inteiro = (digitos.slice(0, -2) || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `R$ ${inteiro},${centavos}`;
  },
  cpf(valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 11);
    return digitos
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  },
  cep(valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 8);
    return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos;
  },
  data_nascimento(valor) {
    const digitos = valor.replace(/\D/g, "").slice(0, 8);
    return digitos.replace(/(\d{2})(\d)/, "$1/$2").replace(/(\d{2})(\d)/, "$1/$2");
  },
};

function abrirAba(aba) {
  document.querySelectorAll(".aba").forEach((botao) => {
    botao.classList.toggle("ativa", botao.dataset.aba === aba);
  });
  document.querySelectorAll(".formulario").forEach((formulario) => {
    formulario.classList.toggle("oculto", formulario.dataset.aba !== aba);
  });
}

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => abrirAba(botao.dataset.aba));
});

document.querySelectorAll(".formulario").forEach((formulario) => {
  formulario.addEventListener("focusout", (evento) => {
    const formatar = FORMATADORES[evento.target.name];
    if (formatar) evento.target.value = formatar(evento.target.value);
  });

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const aba = formulario.dataset.aba;
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ aba, ...Object.fromEntries(new FormData(formulario)) }),
    });
    const dados = await resposta.();
    if (dados.erros) {
      const caixa = document.getElementById(`erros-${aba}`);
      caixa.replaceChildren(
        ...dados.erros.map((mensagem) => {
          const paragrafo = document.createElement("p");
          paragrafo.textContent = mensagem;
          return paragrafo;
        })
      );
      caixa.classList.remove("oculto");
    } else {
      document.getElementById("oficio").textContent = dados.oficio;
      document.getElementById("form-view").classList.add("oculto");
      document.getElementById("confirmacao").classList.remove("oculto");
    }
  });
});
