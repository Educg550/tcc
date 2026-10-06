const formatadores = {
  valor: (v) => {
    const d = v.replace(/\D/g, "");
    if (!d) return "";
    const partes = (parseInt(d, 10) / 100).toFixed(2).split(".");
    partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `R$ ${partes[0]},${partes[1]}`;
  },
  cpf: (v) => {
    const d = v.replace(/\D/g, "").slice(0, 11);
    let out = d.slice(0, 3);
    if (d.length > 3) out += "." + d.slice(3, 6);
    if (d.length > 6) out += "." + d.slice(6, 9);
    if (d.length > 9) out += "-" + d.slice(9, 11);
    return out;
  },
  cep: (v) => {
    const d = v.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  data_nascimento: (v) => {
    const d = v.replace(/\D/g, "").slice(0, 8);
    let out = d.slice(0, 2);
    if (d.length > 2) out += "/" + d.slice(2, 4);
    if (d.length > 4) out += "/" + d.slice(4, 8);
    return out;
  },
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".aba").forEach((aba) => {
    aba.addEventListener("click", () => {
      document.querySelectorAll(".aba").forEach((outra) => {
        outra.classList.toggle("ativa", outra === aba);
      });
      document.querySelectorAll(".painel").forEach((painel) => {
        painel.hidden = painel.id !== aba.dataset.alvo;
      });
    });
  });

  document.querySelectorAll("[data-formatar]").forEach((campo) => {
    campo.addEventListener("blur", () => {
      const formatar = formatadores[campo.dataset.formatar];
      if (formatar) campo.value = formatar(campo.value);
    });
  });

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const dados = Object.fromEntries(new FormData(form).entries());
      const resposta = await fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      });
      const resultado = await resposta.json();
      const erros = form.querySelector(".erros");

      if (resultado.erros && resultado.erros.length) {
        erros.textContent = "";
        resultado.erros.forEach((mensagem) => {
          const linha = document.createElement("div");
          linha.textContent = mensagem;
          erros.appendChild(linha);
        });
        erros.hidden = false;
        return;
      }

      document.getElementById("formulario").hidden = true;
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("confirmacao").hidden = false;
    });
  });
});
