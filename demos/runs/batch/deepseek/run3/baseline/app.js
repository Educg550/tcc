const FORMATOS = {
  moeda: (valor) => {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    const numero = parseInt(digitos, 10);
    const reais = String(Math.floor(numero / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    const centavos = String(numero % 100).padStart(2, "0");
    return "R$ " + reais + "," + centavos;
  },
  cpf: (valor) => {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  },
  cep: (valor) => {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    return d.length <= 5 ? d : d.slice(0, 5) + "-" + d.slice(5);
  },
  data: (valor) => {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  },
};

document.querySelectorAll("[data-formato]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = FORMATOS[campo.dataset.formato](campo.value);
  });
});

/* ---------- Abas ---------- */

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    const aba = botao.dataset.aba;
    document.querySelectorAll(".aba").forEach((outro) => {
      const ativa = outro === botao;
      outro.classList.toggle("ativa", ativa);
      outro.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    document.getElementById("form-alunos").hidden = aba !== "alunos";
    document.getElementById("form-docentes").hidden = aba !== "docentes";
  });
});

/* ---------- Envio ---------- */

document.querySelectorAll(".formulario").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    formulario.querySelectorAll("[data-formato]").forEach((campo) => {
      campo.value = FORMATOS[campo.dataset.formato](campo.value);
    });

    const dados = { aba: formulario.dataset.aba };
    formulario.querySelectorAll("[name]").forEach((campo) => {
      dados[campo.name] = campo.value.trim();
    });

    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    const caixaErros = formulario.querySelector(".erros");

    if (resultado.ok) {
      caixaErros.hidden = true;
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("view-form").hidden = true;
      document.getElementById("view-confirmacao").hidden = false;
    } else {
      caixaErros.replaceChildren(
        ...resultado.erros.map((mensagem) => {
          const linha = document.createElement("div");
          linha.textContent = mensagem;
          return linha;
        })
      );
      caixaErros.hidden = false;
    }
  });
});
