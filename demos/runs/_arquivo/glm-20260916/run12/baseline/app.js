const MASCARAS = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};
const ABAS = ["alunos", "docentes"];

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(texto) {
  const d = digitos(texto);
  if (!d) return "";
  const centavos = parseInt(d, 10);
  const inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + inteiro + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCPF(texto) {
  const d = digitos(texto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCEP(texto) {
  const d = digitos(texto).slice(0, 8);
  return d.length <= 5 ? d : d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

for (const nome of ABAS) {
  document.getElementById("aba-" + nome).addEventListener("click", () => {
    for (const outra of ABAS) {
      const ativa = outra === nome;
      document.getElementById("aba-" + outra).classList.toggle("ativa", ativa);
      document.getElementById("aba-" + outra).setAttribute("aria-selected", String(ativa));
      document.getElementById("painel-" + outra).classList.toggle("oculto", !ativa);
    }
  });
}

for (const campo of document.querySelectorAll("[data-mascara]")) {
  campo.addEventListener("blur", () => {
    campo.value = MASCARAS[campo.dataset.mascara](campo.value);
  });
}

function coletarDados(form, aba) {
  const dados = { aba: aba };
  for (const [chave, valor] of new FormData(form)) {
    dados[chave] = valor.trim();
  }
  for (const campo of form.querySelectorAll("[data-mascara]")) {
    if (campo.name === "valor") {
      dados.valor = digitos(dados.valor || "");
    } else {
      dados[campo.name] = MASCARAS[campo.dataset.mascara](dados[campo.name] || "");
    }
  }
  return dados;
}

function mostrarErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.replaceChildren();
  for (const erro of erros) {
    const linha = document.createElement("p");
    linha.textContent = erro;
    caixa.appendChild(linha);
  }
  caixa.hidden = false;
}

function mostrarOficio(oficio) {
  document.getElementById("conteudo-principal").classList.add("oculto");
  document.getElementById("oficio").textContent = oficio;
  document.getElementById("confirmacao").classList.remove("oculto");
}

for (const nome of ABAS) {
  const form = document.getElementById("form-" + nome);
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(coletarDados(form, nome)),
    });
    const resultado = await resposta.();
    if (resultado.erros) {
      mostrarErros(form, resultado.erros);
    } else {
      mostrarOficio(resultado.oficio);
    }
  });
}
