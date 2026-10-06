function formatarMoeda(texto) {
  const digitos = texto.replace(/\D/g, "");
  if (!digitos) return "";
  const total = parseInt(digitos, 10);
  const reais = Math.floor(total / 100)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const centavos = String(total % 100).padStart(2, "0");
  return `R$ ${reais},${centavos}`;
}

function formatarCPF(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 11);
  if (d.length > 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  if (d.length > 6) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  if (d.length > 3) return `${d.slice(0, 3)}.${d.slice(3)}`;
  return d;
}

function formatarCEP(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 8);
  if (d.length > 5) return `${d.slice(0, 5)}-${d.slice(5)}`;
  return d;
}

function formatarData(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 8);
  if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
  if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return d;
}

const FORMATADORES = {
  valor: formatarMoeda,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData,
};

function formatarCampos(form) {
  form.querySelectorAll("input[name]").forEach((campo) => {
    const formatar = FORMATADORES[campo.name];
    if (formatar) campo.value = formatar(campo.value);
  });
}

document.querySelectorAll(".formulario input[name]").forEach((campo) => {
  const formatar = FORMATADORES[campo.name];
  if (formatar) {
    campo.addEventListener("blur", () => {
      campo.value = formatar(campo.value);
    });
  }
});

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".formulario").forEach((form) => {
      form.classList.toggle("ativo", form.dataset.aba === aba.dataset.aba);
    });
  });
});

document.querySelectorAll(".formulario").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    formatarCampos(form);

    const campos = {};
    new FormData(form).forEach((valor, nome) => {
      campos[nome] = valor;
    });

    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba: form.dataset.aba, campos }),
    });
    const dados = await resposta.json();
    const areaErros = form.querySelector(".erros");

    if (dados.ok) {
      document.getElementById("oficio").textContent = dados.oficio;
      document.getElementById("vista-formulario").classList.add("oculto");
      document.getElementById("vista-confirmacao").classList.remove("oculto");
      window.scrollTo(0, 0);
    } else {
      areaErros.replaceChildren();
      dados.erros.forEach((mensagem) => {
        const linha = document.createElement("div");
        linha.textContent = mensagem;
        areaErros.appendChild(linha);
      });
    }
  });
});
