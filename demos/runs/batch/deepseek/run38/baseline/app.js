const apenasDigitos = (valor) => valor.replace(/\D/g, "");

function formataValor(digitos) {
  digitos = digitos.replace(/^0+(?=\d)/, "");
  if (!digitos) return "";
  const reais = digitos.slice(0, -2) || "0";
  const centavos = digitos.slice(-2).padStart(2, "0");
  return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + centavos;
}

const formataCpf = (d) =>
  d.length === 11 ? d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9) : d;

const formataCep = (d) => (d.length === 8 ? d.slice(0, 5) + "-" + d.slice(5) : d);

const formataData = (d) =>
  d.length === 8 ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4) : d;

/* Abas */
const abas = document.querySelectorAll(".aba");

function trocarAba(aba) {
  abas.forEach((botao) => {
    const ativa = botao.dataset.aba === aba;
    botao.classList.toggle("ativa", ativa);
    botao.setAttribute("aria-selected", String(ativa));
  });
  document.getElementById("form-alunos").hidden = aba !== "alunos";
  document.getElementById("form-docentes").hidden = aba !== "docentes";
}

abas.forEach((botao) => botao.addEventListener("click", () => trocarAba(botao.dataset.aba)));

/* Campos que se formatam sozinhos */
document.querySelectorAll('[name="valor"]').forEach((campo) => {
  campo.addEventListener("input", () => {
    campo.value = formataValor(apenasDigitos(campo.value));
  });
});

[
  ["cpf", formataCpf],
  ["cep", formataCep],
  ["data_nascimento", formataData],
].forEach(([nome, formatar]) => {
  document.querySelectorAll('[name="' + nome + '"]').forEach((campo) => {
    campo.addEventListener("blur", () => {
      const digitos = apenasDigitos(campo.value);
      const formatado = formatar(digitos);
      if (formatado !== digitos) campo.value = formatado;
    });
  });
});

/* Envio */
document.querySelectorAll(".formulario").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const aba = formulario.id === "form-docentes" ? "docentes" : "alunos";

    const dados = { aba };
    new FormData(formulario).forEach((valor, chave) => {
      dados[chave] = valor;
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    const caixa = document.getElementById("erros-" + aba);

    if (!resultado.ok) {
      caixa.textContent = "";
      resultado.erros.forEach((mensagem) => {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      });
      caixa.hidden = false;
      return;
    }

    caixa.hidden = true;
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("app").hidden = true;
    document.getElementById("confirmacao").hidden = false;
  });
});
