const abas = document.querySelectorAll(".aba");
const paineis = document.querySelectorAll(".painel");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
      outra.setAttribute("aria-selected", String(outra === aba));
    });
    paineis.forEach((painel) => {
      painel.classList.toggle("ativo", painel.dataset.aba === aba.dataset.aba);
    });
  });
});

const apenasDigitos = (valor) => (valor || "").replace(/\D/g, "");

function formataValor(valor) {
  const digitos = apenasDigitos(valor);
  if (!digitos) return "";
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100).toLocaleString("pt-BR");
  return `R$ ${reais},${String(centavos % 100).padStart(2, "0")}`;
}

function formataCpf(valor) {
  const digitos = apenasDigitos(valor).slice(0, 11);
  let texto = digitos.slice(0, 3);
  if (digitos.length > 3) texto += "." + digitos.slice(3, 6);
  if (digitos.length > 6) texto += "." + digitos.slice(6, 9);
  if (digitos.length > 9) texto += "-" + digitos.slice(9, 11);
  return texto;
}

function formataCep(valor) {
  const digitos = apenasDigitos(valor).slice(0, 8);
  return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos;
}

function formataData(valor) {
  const digitos = apenasDigitos(valor).slice(0, 8);
  let texto = digitos.slice(0, 2);
  if (digitos.length > 2) texto += "/" + digitos.slice(2, 4);
  if (digitos.length > 4) texto += "/" + digitos.slice(4, 8);
  return texto;
}

const formatadores = {
  valor_solicitado: formataValor,
  cpf: formataCpf,
  cep: formataCep,
  data_nascimento: formataData,
};

document.querySelectorAll("input[name]").forEach((campo) => {
  const formata = formatadores[campo.name];
  if (formata) {
    campo.addEventListener("blur", () => {
      campo.value = formata(campo.value);
    });
  }
});

paineis.forEach((painel) => {
  painel.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { aba: painel.dataset.aba };
    painel.querySelectorAll("input[name], select[name], textarea[name]").forEach((campo) => {
      dados[campo.name] = campo.value.trim();
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    const caixa = painel.querySelector(".erros");
    if (resultado.erros) {
      caixa.replaceChildren(
        ...resultado.erros.map((erro) => {
          const linha = document.createElement("div");
          linha.textContent = erro;
          return linha;
        })
      );
      caixa.hidden = false;
      return;
    }
    caixa.hidden = true;
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("area-formularios").hidden = true;
    document.querySelector("nav.abas").hidden = true;
    document.getElementById("confirmacao").hidden = false;
  });
});
