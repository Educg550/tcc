function digitos(v) {
  return (v || "").replace(/\D/g, "");
}

function mascaraValor(v) {
  const d = digitos(v);
  if (!d) return "";
  const n = parseInt(d, 10);
  return "R$ " + Math.floor(n / 100).toLocaleString("pt-BR") + "," + String(n % 100).padStart(2, "0");
}

function mascaraCPF(v) {
  const d = digitos(v).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function mascaraCEP(v) {
  const d = digitos(v).slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function mascaraData(v) {
  const d = digitos(v).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

const mascaras = {
  valor: mascaraValor,
  cpf: mascaraCPF,
  cep: mascaraCEP,
  data_nascimento: mascaraData,
};

document.querySelectorAll("input").forEach(function (input) {
  const mascara = mascaras[input.name];
  if (mascara) {
    input.addEventListener("blur", function () {
      input.value = mascara(input.value);
    });
  }
});

const abas = document.querySelectorAll(".aba");
abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".painel").forEach(function (painel) {
      painel.classList.toggle("ativo", painel.dataset.form === aba.dataset.aba);
    });
  });
});

function mostrarErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.textContent = (erros || []).join("\n");
  caixa.style.display = erros && erros.length ? "block" : "none";
}

document.querySelectorAll(".painel").forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const dados = {};
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    dados.aba = form.dataset.form;

    const resposta = await fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    if (resultado.ok) {
      document.getElementById("formulario").style.display = "none";
      document.getElementById("confirmacao").style.display = "block";
      document.getElementById("oficio").textContent = resultado.oficio;
    } else {
      mostrarErros(form, resultado.erros);
    }
  });
});
