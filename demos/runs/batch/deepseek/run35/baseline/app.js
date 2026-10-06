const soDigitos = (valor) => valor.replace(/\D/g, "");

const fmtMoeda = (valor) => {
  const digitos = soDigitos(valor);
  if (!digitos) return "";
  const n = parseInt(digitos, 10);
  const reais = Math.floor(n / 100).toLocaleString("pt-BR");
  return `R$ ${reais},${String(n % 100).padStart(2, "0")}`;
};

const fmtCpf = (valor) => {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
  return d;
};

const fmtCep = (valor) => {
  const d = soDigitos(valor).slice(0, 8);
  return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
};

const fmtData = (valor) => {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
  if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return d;
};

const FORMATADORES = { moeda: fmtMoeda, cpf: fmtCpf, cep: fmtCep, data: fmtData };

document.querySelectorAll("[data-fmt]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = FORMATADORES[campo.dataset.fmt](campo.value);
  });
});

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((b) => b.classList.remove("ativo"));
    document.querySelectorAll(".painel").forEach((p) => p.classList.remove("ativo"));
    botao.classList.add("ativo");
    document.getElementById("painel-" + botao.dataset.aba).classList.add("ativo");
  });
});

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const dados = {};
    new FormData(form).forEach((valor, chave) => { dados[chave] = valor; });

    const resposta = await fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: form.dataset.aba, dados }),
    });
    const resultado = await resposta.json();

    const areaErros = form.querySelector(".erros");
    if (resultado.erros && resultado.erros.length) {
      areaErros.textContent = "";
      resultado.erros.forEach((mensagem) => {
        const linha = document.createElement("div");
        linha.textContent = mensagem;
        areaErros.appendChild(linha);
      });
      areaErros.classList.remove("oculto");
      return;
    }

    areaErros.textContent = "";
    areaErros.classList.add("oculto");
    document.getElementById("principal").classList.add("oculto");
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("confirmacao").classList.remove("oculto");
  });
});
