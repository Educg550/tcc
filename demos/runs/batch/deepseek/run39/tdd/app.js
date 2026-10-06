const apenasDigitos = (valor) => (valor || "").replace(/\D/g, "");

function formatarMoeda(digitos) {
  digitos = digitos.replace(/^0+/, "");
  if (!digitos) return "";
  const centavos = digitos.padStart(3, "0");
  const reais = centavos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `R$ ${reais},${centavos.slice(-2)}`;
}

function formatarCpf(digitos) {
  const d = digitos.slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

function formatarCep(digitos) {
  const d = digitos.slice(0, 8);
  return d.length <= 5 ? d : `${d.slice(0, 5)}-${d.slice(5)}`;
}

function formatarData(digitos) {
  const d = digitos.slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

const mascaras = {
  valor: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

document.querySelectorAll("input").forEach((input) => {
  const formatar = mascaras[input.name];
  if (!formatar) return;
  const aplicar = () => {
    input.value = formatar(apenasDigitos(input.value));
  };
  input.addEventListener("input", aplicar);
  input.addEventListener("blur", aplicar);
});

// Abas

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outro) => {
      const ativa = outro === botao;
      outro.classList.toggle("ativa", ativa);
      outro.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    document.querySelectorAll(".formulario").forEach((secao) => {
      secao.classList.toggle("ativo", secao.id === `form-${botao.dataset.aba}`);
    });
  });
});

// Envio

function mostrarErros(aba, mensagens) {
  const caixa = document.getElementById(`erros-${aba}`);
  caixa.textContent = "";
  mensagens.forEach((mensagem) => {
    const linha = document.createElement("p");
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
}

function mostrarConfirmacao(oficio) {
  document.querySelector(".abas").hidden = true;
  document.querySelectorAll(".formulario").forEach((secao) => secao.classList.remove("ativo"));
  document.getElementById("oficio").textContent = oficio;
  document.getElementById("confirmacao").classList.add("ativo");
}

document.querySelectorAll("form[data-aba]").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const aba = form.dataset.aba;
    const dados = Object.fromEntries(new FormData(form).entries());
    const resposta = await fetch(`/solicitacao/${aba}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.json();
    if (resposta.ok) {
      mostrarConfirmacao(corpo.oficio);
    } else {
      mostrarErros(aba, corpo.erros);
    }
  });
});
