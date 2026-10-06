const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const d = digitos(texto);
  if (!d) return "";
  const centavos = parseInt(d, 10);
  const reais = String(Math.floor(centavos / 100));
  const resto = String(centavos % 100).padStart(2, "0");
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + resto;
}

function formatarCpf(texto) {
  const d = digitos(texto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(texto) {
  const d = digitos(texto).slice(0, 8);
  return d.length <= 5 ? d : d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

document.querySelectorAll("[data-formato]").forEach((campo) => {
  campo.addEventListener("input", () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.getElementById("painel-alunos").hidden = aba.dataset.aba !== "alunos";
    document.getElementById("painel-docentes").hidden = aba.dataset.aba !== "docentes";
  });
});

function ligarEnvio(idForm, idErros) {
  const form = document.getElementById(idForm);
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const corpo = {};
    form.querySelectorAll("[name]").forEach((campo) => {
      corpo[campo.name] = campo.value;
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(corpo),
    });
    const dados = await resposta.();
    const caixa = document.getElementById(idErros);
    if (dados.erros) {
      caixa.textContent = dados.erros.join("\n");
      return;
    }
    caixa.textContent = "";
    document.getElementById("conteudo").hidden = true;
    document.getElementById("oficio").textContent = dados.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
}

ligarEnvio("form-alunos", "erros-alunos");
ligarEnvio("form-docentes", "erros-docentes");
