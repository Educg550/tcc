function fmtMoeda(valor) {
  const digitos = valor.replace(/\D/g, "");
  if (!digitos) return "";
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function fmtCpf(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function fmtCep(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function fmtData(valor) {
  const d = valor.replace(/\D/g, "").slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

const FORMATOS = { moeda: fmtMoeda, cpf: fmtCpf, cep: fmtCep, data: fmtData };

document.querySelectorAll("[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = FORMATOS[campo.dataset.formato](campo.value);
  });
});

const abas = document.querySelectorAll(".aba");
const formularios = document.querySelectorAll(".formulario");

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    formularios.forEach(function (form) {
      form.hidden = form.dataset.aba !== aba.dataset.aba;
    });
  });
});

formularios.forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();

    form.querySelectorAll("[data-formato]").forEach(function (campo) {
      campo.value = FORMATOS[campo.dataset.formato](campo.value);
    });

    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    }).then(function (r) { return r.json(); });

    const caixaErros = form.querySelector(".erros");

    if (!resposta.ok) {
      caixaErros.innerHTML = "";
      resposta.erros.forEach(function (mensagem) {
        const linha = document.createElement("div");
        linha.textContent = mensagem;
        caixaErros.appendChild(linha);
      });
      caixaErros.hidden = false;
      return;
    }

    caixaErros.hidden = true;
    document.getElementById("abas").hidden = true;
    formularios.forEach(function (f) { f.hidden = true; });
    document.getElementById("oficio").textContent = resposta.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
});
