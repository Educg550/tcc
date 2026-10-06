const areaFormulario = document.getElementById("area-formulario");
const confirmacao = document.getElementById("confirmacao");
const oficio = document.getElementById("oficio");

const abas = document.querySelectorAll(".aba");

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((outra) => outra.classList.toggle("ativa", outra === aba));
    document.querySelectorAll(".painel").forEach((painel) => {
      painel.classList.toggle("ativo", painel.dataset.aba === aba.dataset.aba);
    });
  });
});

function moeda(valor) {
  const d = valor.replace(/\D/g, "");
  if (!d) return "";
  const inteiro = (d.slice(0, -2) || "0").replace(/\B(?=(\d{3})+$)/g, ".");
  return `R$ ${inteiro},${d.slice(-2).padStart(2, "0")}`;
}

function cpf(valor) {
  return valor
    .replace(/\D/g, "")
    .slice(0, 11)
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
}

function cep(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}

function data(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
}

const mascaras = { valor: moeda, cpf, cep, data_nascimento: data };

document.querySelectorAll(".painel input").forEach((campo) => {
  const mascara = mascaras[campo.name];
  if (mascara) {
    campo.addEventListener("blur", () => {
      campo.value = mascara(campo.value);
    });
  }
});

document.querySelectorAll(".painel").forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const campos = {};
    new FormData(formulario).forEach((valor, chave) => {
      campos[chave] = String(valor).trim();
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: formulario.dataset.aba, campos }),
    });
    const dados = await resposta.json();

    const caixa = formulario.querySelector(".erros");
    caixa.textContent = "";

    if (dados.erros.length) {
      dados.erros.forEach((mensagem) => {
        const linha = document.createElement("p");
        linha.textContent = mensagem;
        caixa.appendChild(linha);
      });
      caixa.hidden = false;
      return;
    }

    caixa.hidden = true;
    oficio.textContent = dados.oficio;
    areaFormulario.hidden = true;
    confirmacao.hidden = false;
  });
});
