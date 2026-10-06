const formatadores = {
  moeda: v => {
    const d = v.replace(/\D/g, "");
    if (!d) return "";
    const n = parseInt(d, 10);
    return "R$ " + (n / 100).toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  },
  cpf: v => {
    const d = v.replace(/\D/g, "").slice(0, 11);
    if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
    if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
    return d;
  },
  cep: v => {
    const d = v.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  data: v => {
    const d = v.replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
    if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`;
    return d;
  },
};

document.querySelectorAll("[data-format]").forEach(campo => {
  campo.addEventListener("blur", () => {
    campo.value = formatadores[campo.dataset.format](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
abas.forEach(aba => {
  aba.addEventListener("click", () => {
    abas.forEach(a => a.classList.toggle("ativa", a === aba));
    document.querySelectorAll(".formulario").forEach(form => {
      form.hidden = form.dataset.aba !== aba.dataset.aba;
    });
  });
});

document.querySelectorAll(".formulario").forEach(form => {
  form.addEventListener("submit", async evento => {
    evento.preventDefault();

    const dados = { aba: form.dataset.aba };
    form.querySelectorAll("[name]").forEach(campo => {
      dados[campo.name] = campo.value.trim();
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    const erros = form.querySelector(".erros");
    if (resultado.erros.length) {
      erros.textContent = resultado.erros.join("\n");
      erros.hidden = false;
    } else {
      erros.hidden = true;
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("conteudo").hidden = true;
      document.getElementById("confirmacao").hidden = false;
    }
  });
});
