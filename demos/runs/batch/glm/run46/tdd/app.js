"use strict";

const CAMPOS = [
  "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
  "nome_evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
  "link_evento", "valor", "detalhamento", "apresentacao", "data_nascimento",
  "logradouro", "numero", "complemento", "bairro", "cep", "cidade", "estado",
  "cpf", "rg", "banco", "agencia", "conta",
];

const MASCARAS = {
  valor(d) {
    const centavos = parseInt(d, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
  },
  cpf(d) {
    return d.length === 11
      ? d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9)
      : d;
  },
  cep(d) {
    return d.length === 8 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  },
  data_nascimento(d) {
    return d.length === 8 ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4) : d;
  },
};

document.querySelectorAll("[data-formato]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    const digitos = campo.value.replace(/\D/g, "");
    campo.value = digitos ? MASCARAS[campo.dataset.formato](digitos) : "";
  });
});

const abas = document.querySelectorAll(".aba");
const paineis = {
  aluno: document.getElementById("painel-aluno"),
  docente: document.getElementById("painel-docente"),
};

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    Object.keys(paineis).forEach((tipo) => {
      paineis[tipo].hidden = tipo !== aba.dataset.aba;
    });
  });
});

function coletar(form, tipo) {
  const dados = { tipo };
  CAMPOS.forEach((nome) => {
    const campo = form.elements[nome];
    if (!campo) {
      return;
    }
    const bruto = campo.value.trim();
    dados[nome] = MASCARAS[nome] ? bruto.replace(/\D/g, "") : bruto;
  });
  return dados;
}

function mostrarErros(form, erros) {
  const lista = form.querySelector(".erros");
  lista.innerHTML = "";
  erros.forEach((mensagem) => {
    const item = document.createElement("li");
    item.textContent = mensagem;
    lista.appendChild(item);
  });
  lista.hidden = erros.length === 0;
}

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletar(form, form.dataset.tipo)),
    });
    const corpo = await resposta.json();
    if (!corpo.ok) {
      mostrarErros(form, corpo.erros);
      return;
    }
    document.getElementById("oficio").textContent = corpo.oficio;
    document.getElementById("pagina-formulario").hidden = true;
    document.getElementById("pagina-confirmacao").hidden = false;
  });
});
