const NAO_DIGITO = /\D/g;

function apenasDigitos(texto) {
  return texto.replace(NAO_DIGITO, "");
}

function formatarValor(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 12);
  if (!digitos) {
    campo.value = "";
    return;
  }
  const centavos = digitos.slice(-2).padStart(2, "0");
  const reais =
    digitos.slice(0, -2).replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".") || "0";
  campo.value = "R$ " + reais + "," + centavos;
}

function formatarCpf(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 11);
  let formatado = digitos.slice(0, 3);
  if (digitos.length > 3) formatado += "." + digitos.slice(3, 6);
  if (digitos.length > 6) formatado += "." + digitos.slice(6, 9);
  if (digitos.length > 9) formatado += "-" + digitos.slice(9, 11);
  campo.value = formatado;
}

function formatarCep(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 8);
  campo.value = digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(campo) {
  const digitos = apenasDigitos(campo.value).slice(0, 8);
  let formatado = digitos.slice(0, 2);
  if (digitos.length > 2) formatado += "/" + digitos.slice(2, 4);
  if (digitos.length > 4) formatado += "/" + digitos.slice(4, 8);
  campo.value = formatado;
}

[
  [".campo-valor", formatarValor],
  [".campo-cpf", formatarCpf],
  [".campo-cep", formatarCep],
  [".campo-data", formatarData],
].forEach(function (par) {
  document.querySelectorAll(par[0]).forEach(function (campo) {
    campo.addEventListener("blur", function () {
      par[1](campo);
    });
  });
});

function mostrarAba(nome) {
  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.classList.toggle("ativa", botao.dataset.aba === nome);
  });
  document.getElementById("form-alunos").classList.toggle("oculto", nome !== "alunos");
  document.getElementById("form-docentes").classList.toggle("oculto", nome !== "docentes");
}

document.getElementById("aba-alunos").addEventListener("click", function () {
  mostrarAba("alunos");
});
document.getElementById("aba-docentes").addEventListener("click", function () {
  mostrarAba("docentes");
});

async function enviarSolicitacao(formulario) {
  const dados = new FormData(formulario);
  const campoValor = formulario.querySelector(".campo-valor");
  if (campoValor) {
    dados.set("valor_solicitado", apenasDigitos(campoValor.value));
  }
  const resposta = await fetch("/api/solicitacao", { method: "POST", body: dados });
  const texto = await resposta.text();
  if (resposta.ok) {
    document.getElementById("formularios").classList.add("oculto");
    document.getElementById("oficio").textContent = texto;
    document.getElementById("confirmacao").classList.remove("oculto");
  } else {
    const mensagens = formulario.querySelector(".mensagens");
    mensagens.innerHTML = "";
    texto.split("\n").forEach(function (linha) {
      const paragrafo = document.createElement("p");
      paragrafo.textContent = linha;
      mensagens.appendChild(paragrafo);
    });
  }
}

document.querySelectorAll("form").forEach(function (formulario) {
  formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();
    enviarSolicitacao(formulario);
  });
});
