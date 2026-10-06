"use strict";

function apenasDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

function formatarValor(cents) {
  var inteiro = Math.floor(cents / 100);
  var centavos = cents % 100;
  return "R$ " + String(inteiro).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + String(centavos).padStart(2, "0");
}

function formatarCpf(digitos) {
  digitos = apenasDigitos(digitos).slice(0, 11);
  var partes = digitos.match(/.{1,3}/g) || [];
  var t = partes.slice(0, 3).join(".");
  if (digitos.length > 9) {
    t += "-" + partes[3];
  }
  return t;
}

function formatarCep(digitos) {
  digitos = apenasDigitos(digitos).slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(digitos) {
  digitos = apenasDigitos(digitos).slice(0, 8);
  var partes = digitos.match(/.{1,2}/g) || [];
  return partes.join("/");
}

/* ===== Abas ===== */

var botoesAba = document.querySelectorAll(".aba");
botoesAba.forEach(function (botao) {
  botao.addEventListener("click", function () {
    botoesAba.forEach(function (b) {
      b.classList.toggle("ativa", b === botao);
      b.setAttribute("aria-selected", b === botao ? "true" : "false");
    });
    document.getElementById("form-alunos").hidden = botao.dataset.aba !== "alunos";
    document.getElementById("form-docentes").hidden = botao.dataset.aba !== "docentes";
    document.getElementById("conteudo").hidden = false;
    document.getElementById("confirmacao").hidden = true;
  });
});

/* ===== Máscaras ao sair do campo ===== */

document.querySelectorAll("input[name='valor']").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formatarValor(parseInt(apenasDigitos(campo.value) || "0", 10));
  });
});

document.querySelectorAll("input[name='cpf']").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formatarCpf(campo.value);
  });
});

document.querySelectorAll("input[name='cep']").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formatarCep(campo.value);
  });
});

document.querySelectorAll("input[name='nascimento']").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = formatarData(campo.value);
  });
});

/* ===== Envio ===== */

document.querySelectorAll("form.formulario").forEach(function (form) {
  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    var aba = form.id === "form-alunos" ? "alunos" : "docentes";
    var caixaErros = document.getElementById("erros-" + aba);

    var dados = { aba: aba };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = typeof valor === "string" ? valor.trim() : valor;
    });

    var resposta;
    try {
      resposta = await fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      });
    } catch (falha) {
      caixaErros.hidden = false;
      caixaErros.textContent = "Falha ao comunicar com o servidor";
      return;
    }

    var corpo = await resposta.json();

    if (resposta.ok) {
      caixaErros.hidden = true;
      caixaErros.textContent = "";
      document.getElementById("conteudo").hidden = true;
      document.getElementById("oficio").textContent = corpo.oficio;
      document.getElementById("confirmacao").hidden = false;
    } else {
      caixaErros.hidden = false;
      caixaErros.textContent = corpo.erros.join("\n");
      caixaErros.scrollIntoView();
    }
  });
});
