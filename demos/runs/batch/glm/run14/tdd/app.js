"use strict";

function apenasDigitos(valor) {
  return valor.replace(/\D/g, "");
}

function formatarValor(valor) {
  const digitos = apenasDigitos(valor);
  if (!digitos) return "";
  const centavos = parseInt(digitos, 10);
  const reais = Math.floor(centavos / 100);
  const parteInteira = reais.toLocaleString("pt-BR");
  return "R$ " + parteInteira + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCpf(valor) {
  const d = apenasDigitos(valor).slice(0, 11);
  if (d.length !== 11) return valor;
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  if (d.length !== 8) return valor;
  return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(valor) {
  const d = apenasDigitos(valor).slice(0, 8);
  if (d.length !== 8) return valor;
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const FORMATACOES = [
  { classe: "campo-valor", fn: formatarValor },
  { classe: "campo-cpf", fn: formatarCpf },
  { classe: "campo-cep", fn: formatarCep },
  { classe: "campo-data", fn: formatarData },
];

document.addEventListener("DOMContentLoaded", function () {
  FORMATACOES.forEach(function (item) {
    document.querySelectorAll("." + item.classe + " input").forEach(function (input) {
      input.addEventListener("blur", function () {
        if (input.value.trim() !== "") {
          input.value = item.fn(input.value);
        }
      });
    });
  });

  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (outra) {
        outra.classList.remove("ativa");
        outra.setAttribute("aria-selected", "false");
      });
      aba.classList.add("ativa");
      aba.setAttribute("aria-selected", "true");
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.hidden = true;
      });
      document.getElementById(aba.dataset.painel).hidden = false;
    });
  });

  function enviar(form, tipo, listaErros) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      const dados = { tipo: tipo };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (corpo) {
          if (corpo.erros && corpo.erros.length > 0) {
            listaErros.hidden = false;
            listaErros.textContent = "";
            corpo.erros.forEach(function (erro) {
              const linha = document.createElement("p");
              linha.textContent = erro;
              listaErros.appendChild(linha);
            });
            return;
          }
          document.querySelectorAll("main > section").forEach(function (secao) {
            secao.hidden = true;
          });
          document.getElementById("oficio").textContent = corpo.oficio;
          document.getElementById("confirmacao").hidden = false;
        });
    });
  }

  enviar(document.getElementById("form-alunos"), "alunos", document.getElementById("erros-alunos"));
  enviar(document.getElementById("form-docentes"), "docentes", document.getElementById("erros-docentes"));

  document.getElementById("nova-solicitacao").addEventListener("click", function () {
    document.getElementById("confirmacao").hidden = true;
    document.querySelector(".painel").hidden = false;
  });
});
