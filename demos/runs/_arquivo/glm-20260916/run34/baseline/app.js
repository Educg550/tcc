function soDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarMoeda(valor) {
  const digitos = soDigitos(valor);
  if (!digitos) return "";
  let numeros = String(parseInt(digitos, 10));
  if (numeros.length < 3) numeros = numeros.padStart(3, "0");
  const centavos = numeros.slice(-2);
  const reais = numeros.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + centavos;
}

function formatarCpf(valor) {
  const d = soDigitos(valor).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length <= 5) return d;
  return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(valor) {
  const d = soDigitos(valor).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const FORMATADORES = { moeda: formatarMoeda, cpf: formatarCpf, cep: formatarCep, data: formatarData };

document.querySelectorAll("input[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".formulario").forEach(function (form) {
      form.classList.toggle("oculto", form.dataset.origem !== aba.dataset.aba);
    });
  });
});

document.querySelectorAll(".formulario").forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const dados = {};
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ origem: form.dataset.origem, dados: dados })
    });
    const resultado = await resposta.();
    const areaErros = form.querySelector(".erros");
    if (resultado.erros && resultado.erros.length) {
      areaErros.innerHTML = "";
      resultado.erros.forEach(function (mensagem) {
        const linha = document.createElement("div");
        linha.textContent = mensagem;
        areaErros.appendChild(linha);
      });
      return;
    }
    document.getElementById("oficio").textContent = resultado.oficio;
    document.getElementById("formularios").classList.add("oculto");
    document.getElementById("confirmacao").classList.remove("oculto");
  });
});
