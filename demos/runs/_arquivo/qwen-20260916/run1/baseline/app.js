const apenasDigitos = (v) => v.replace(/\D/g, "");

const formatos = {
  valor_solicitado: (v) => {
    const centavos = apenasDigitos(v);
    if (!centavos) return "";
    const inteiro = centavos.slice(0, -2) || "0";
    const dec = centavos.slice(-2);
    return "R$ " + inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + dec;
  },
  cpf: (v) => {
    const d = apenasDigitos(v).slice(0, 11);
    return d.replace(/^(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})/, (m, a, b, c, e) =>
      a + (b || c || e ? "." + b : "") + (c || e ? "." + c : "") + (e ? "-" + e : "")).replace(/^\./, "");
  },
  cep: (v) => {
    const d = apenasDigitos(v).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data_nascimento: (v) => {
    const d = apenasDigitos(v).slice(0, 8);
    return d.replace(/^(\d{2})(\d{0,2})(\d{0,4})/, (m, a, b, c) =>
      a + (b || c ? "/" + b : "") + (c ? "/" + c : "")).replace(/^\//, "");
  },
};

document.querySelectorAll("input[name]").forEach((campo) => {
  const formatar = formatos[campo.name];
  if (formatar) {
    campo.addEventListener("blur", () => { campo.value = formatar(campo.value); });
  }
});

const botaoAbas = document.querySelectorAll(".aba");
botaoAbas.forEach((botao) => {
  botao.addEventListener("click", () => {
    botaoAbas.forEach((b) => {
      b.classList.remove("ativa");
      b.setAttribute("aria-selected", "false");
    });
    botao.classList.add("ativa");
    botao.setAttribute("aria-selected", "true");
    const aba = botao.dataset.aba;
    document.querySelectorAll(".painel").forEach((p) => {
      p.classList.toggle("ativo", p.id === "form-" + aba);
    });
  });
});

function coletar(form, aba) {
  const dados = { aba: aba };
  form.querySelectorAll("[name]").forEach((campo) => {
    dados[campo.name] = campo.value.trim();
  });
  return dados;
}

document.querySelectorAll("form.painel").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const aba = form.id.replace("form-", "");
    const alvoErros = document.getElementById("erros-" + aba);
    alvoErros.textContent = "";

    const corpo = coletar(form, aba);
    let resposta;
    try {
      resposta = await fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
      });
    } catch (e) {
      alvoErros.textContent = "Falha ao enviar a solicitação";
      return;
    }

    const resultado = await resposta.json();
    if (!resultado.ok) {
      alvoErros.textContent = resultado.erros.join("\n");
      return;
    }

    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("formulario").classList.add("oculta");
    document.getElementById("confirmacao").classList.remove("oculta");
    window.scrollTo(0, 0);
  });
});
