function somenteDigitos(valor, limite) {
  return valor.replace(/\D/g, "").slice(0, limite);
}

function formataMoeda(valor) {
  const digitos = valor.replace(/\D/g, "");
  if (!digitos) return "";
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function formataCPF(valor) {
  const d = somenteDigitos(valor, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += "." + d.slice(3, 6);
  if (d.length > 6) saida += "." + d.slice(6, 9);
  if (d.length > 9) saida += "-" + d.slice(9, 11);
  return saida;
}

function formataCEP(valor) {
  const d = somenteDigitos(valor, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formataData(valor) {
  const d = somenteDigitos(valor, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += "/" + d.slice(2, 4);
  if (d.length > 4) saida += "/" + d.slice(4, 8);
  return saida;
}

const MASCARAS = {
  valor: formataMoeda,
  cpf: formataCPF,
  cep: formataCEP,
  data_nascimento: formataData
};

const abas = document.querySelectorAll(".aba");

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    abas.forEach(function (outra) {
      const ativa = outra === aba;
      outra.classList.toggle("ativa", ativa);
      outra.setAttribute("aria-selected", String(ativa));
      document.getElementById(outra.getAttribute("aria-controls")).hidden = !ativa;
    });
  });
});

async function enviar(evento, form) {
  evento.preventDefault();

  const campos = {};
  new FormData(form).forEach(function (valor, nome) {
    campos[nome] = valor.trim();
  });

  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ aba: form.dataset.aba, campos: campos })
  });
  const dados = await resposta.json();
  const erros = form.querySelector(".erros");

  if (dados.erros && dados.erros.length) {
    erros.textContent = dados.erros.join("\n");
    erros.hidden = false;
    return;
  }

  erros.hidden = true;
  document.getElementById("oficio").textContent = dados.oficio;
  document.getElementById("app-formulario").hidden = true;
  document.getElementById("confirmacao").hidden = false;
}

document.querySelectorAll("form").forEach(function (form) {
  form.querySelectorAll("[name]").forEach(function (campo) {
    const mascara = MASCARAS[campo.name];
    if (mascara) {
      campo.addEventListener("blur", function () {
        campo.value = mascara(campo.value);
      });
    }
  });

  form.addEventListener("submit", function (evento) {
    enviar(evento, form);
  });
});
