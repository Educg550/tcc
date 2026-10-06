const abas = document.querySelectorAll(".aba");
const formularios = document.querySelectorAll(".formulario");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    formularios.forEach((form) => {
      form.hidden = form.dataset.aba !== aba.dataset.aba;
    });
  });
});

const formatadores = {
  valor(valor) {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    const centavos = parseInt(digitos, 10);
    const reais = Math.floor(centavos / 100);
    const resto = String(centavos % 100).padStart(2, "0");
    return "R$ " + reais.toLocaleString("pt-BR") + "," + resto;
  },
  cpf(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
    if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
    return d;
  },
  cep(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  data_nascimento(valor) {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
    if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`;
    return d;
  },
};

formularios.forEach((form) => {
  form.querySelectorAll("input").forEach((campo) => {
    const formatar = formatadores[campo.name];
    if (formatar) {
      campo.addEventListener("blur", () => {
        campo.value = formatar(campo.value);
      });
    }
  });

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const dados = {};
    form.querySelectorAll("input, select, textarea").forEach((campo) => {
      if (campo.name) dados[campo.name] = campo.value;
    });

    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: form.dataset.aba, dados }),
    });
    const resultado = await resposta.json();

    const caixaErros = form.querySelector(".erros");
    caixaErros.textContent = "";
    caixaErros.hidden = true;

    if (resultado.erros && resultado.erros.length) {
      resultado.erros.forEach((mensagem) => {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        caixaErros.appendChild(linha);
      });
      caixaErros.hidden = false;
      return;
    }

    document.getElementById("conteudo").hidden = true;
    document.getElementById("confirmacao").hidden = false;
    document.getElementById("oficio").textContent = resultado.oficio;
  });
});
