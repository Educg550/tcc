const FORMATADORES = {
  valor: (valor) => {
    const digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    const numero = parseInt(digitos, 10) / 100;
    return (
      "R$ " +
      numero.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  },
  cpf: (valor) => {
    const d = valor.replace(/\D/g, "").slice(0, 11);
    if (d.length > 9) {
      return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
    }
    if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
    if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
    return d;
  },
  cep: (valor) => {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
  },
  data_nascimento: (valor) => {
    const d = valor.replace(/\D/g, "").slice(0, 8);
    if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
    if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`;
    return d;
  },
};

document.querySelectorAll("input").forEach((input) => {
  const formata = FORMATADORES[input.name];
  if (!formata) return;
  input.addEventListener("blur", () => {
    input.value = formata(input.value);
  });
});

const abas = document.querySelectorAll(".aba");
const formularios = document.querySelectorAll(".formulario");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    formularios.forEach((formulario) => {
      formulario.classList.toggle("oculto", formulario.dataset.aba !== aba.dataset.aba);
    });
  });
});

formularios.forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = Object.fromEntries(new FormData(formulario));
    const resposta = await fetch(`/api/solicitacao/${formulario.dataset.aba}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    const caixaErros = formulario.querySelector(".erros");
    if (!resposta.ok) {
      caixaErros.textContent = resultado.erros.join("\n");
      return;
    }
    caixaErros.textContent = "";
    document.getElementById("oficio").textContent = resultado.oficio;
    formularios.forEach((item) => item.classList.add("oculto"));
    document.querySelector(".abas").classList.add("oculto");
    document.getElementById("confirmacao").classList.remove("oculto");
  });
});
