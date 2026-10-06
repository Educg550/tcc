"use strict";

function apenasDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const digitos = apenasDigitos(texto);
  if (!digitos) return "";
  const centavos = parseInt(digitos, 10);
  const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCpf(texto) {
  const d = apenasDigitos(texto).slice(0, 11);
  return d
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatarCep(texto) {
  return apenasDigitos(texto).slice(0, 8).replace(/(\d{5})(\d{1,3})$/, "$1-$2");
}

function formatarData(texto) {
  const d = apenasDigitos(texto).slice(0, 8);
  if (d.length > 4) return d.replace(/(\d{2})(\d{2})(\d{1,4})/, "$1/$2/$3");
  if (d.length > 2) return d.replace(/(\d{2})(\d{1,2})/, "$1/$2");
  return d;
}

const FORMATADORES = {
  valor_solicitado: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((b) => b.classList.toggle("ativa", b === botao));
    document.querySelectorAll(".formulario").forEach((f) => {
      f.hidden = f.id !== botao.dataset.alvo;
    });
  });
});

document.querySelectorAll(".formulario").forEach((form) => {
  Object.entries(FORMATADORES).forEach(([nome, formatar]) => {
    const campo = form.elements[nome];
    if (!campo) return;
    campo.addEventListener("blur", () => {
      campo.value = formatar(campo.value);
    });
  });

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    new FormData(form).forEach((valor, chave) => {
      dados[chave] = valor;
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados),
    });
    const corpo = await resposta.();
    if (corpo.valido) {
      document.getElementById("oficio").textContent = corpo.oficio;
      document.getElementById("formulario-view").hidden = true;
      document.getElementById("confirmacao").hidden = false;
      return;
    }
    const aviso = form.querySelector(".erros");
    aviso.replaceChildren();
    corpo.erros.forEach((mensagem) => {
      const paragrafo = document.createElement("p");
      paragrafo.textContent = mensagem;
      aviso.appendChild(paragrafo);
    });
    aviso.hidden = false;
  });
});

document.getElementById("voltar").addEventListener("click", () => {
  document.getElementById("confirmacao").hidden = true;
  document.getElementById("formulario-view").hidden = false;
});
