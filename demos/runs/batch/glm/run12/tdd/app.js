"use strict";

function formatarMoeda(digitos) {
  digitos = (digitos.replace(/\D/g, "") || "0").slice(0, 15);
  let valor = parseInt(digitos, 10);
  let centavos = String(valor % 100).padStart(2, "0");
  let inteiro = String(Math.floor(valor / 100));
  inteiro = inteiro.replace(/(\d)(?=(\d{3})+$)/g, "$1.");
  return "R$ " + inteiro + "," + centavos;
}

function formatarCPF(valor) {
  let d = valor.replace(/\D/g, "").slice(0, 11);
  return d.slice(0, 3) + (d.length > 3 ? "." + d.slice(3, 6) : "") +
    (d.length > 6 ? "." + d.slice(6, 9) : "") + (d.length > 9 ? "-" + d.slice(9) : "");
}

function formatarCEP(valor) {
  let d = valor.replace(/\D/g, "").slice(0, 8);
  return d.slice(0, 5) + (d.length > 5 ? "-" + d.slice(5) : "");
}

function formatarData(valor) {
  let d = valor.replace(/\D/g, "").slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

function aoSairDoCampo(campo, formatar) {
  campo.addEventListener("blur", function () {
    campo.value = formatar(campo.value);
  });
}

document.querySelectorAll('input[name="valor_solicitado"]').forEach(function (c) {
  aoSairDoCampo(c, formatarMoeda);
});
document.querySelectorAll('input[name="cpf"]').forEach(function (c) {
  aoSairDoCampo(c, formatarCPF);
});
document.querySelectorAll('input[name="cep"]').forEach(function (c) {
  aoSairDoCampo(c, formatarCEP);
});
document.querySelectorAll('input[name="data_nascimento"]').forEach(function (c) {
  aoSairDoCampo(c, formatarData);
});

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (b) {
      b.classList.remove("ativa");
    });
    botao.classList.add("ativa");
    document.querySelectorAll(".painel").forEach(function (p) {
      p.classList.add("oculto");
    });
    document.getElementById("aba-" + botao.dataset.aba).classList.remove("oculto");
  });
});

function mostrarErros(aba, erros) {
  var caixa = document.getElementById("erros-" + aba);
  caixa.innerHTML = "";
  erros.forEach(function (mensagem) {
    var li = document.createElement("li");
    li.textContent = mensagem;
    caixa.appendChild(li);
  });
}

function enviarSolicitacao(aba, form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var dados = {
      aba: aba,
    };
    new FormData(form).forEach(function (valor, nome) {
      dados[nome] = valor.trim();
    });
    if (aba === "docentes") {
      delete dados.nivel;
      delete dados.tipo_auxilio;
    }
    fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then(function (r) { return r.json(); })
      .then(function (corpo) {
        if (corpo.erros) {
          mostrarErros(aba, corpo.erros);
        } else {
          document.getElementById("oficio").textContent = corpo.oficio;
          document.querySelectorAll(".painel").forEach(function (p) {
            p.classList.add("oculto");
          });
          document.querySelector(".abas").classList.add("oculto");
          document.getElementById("confirmacao").classList.remove("oculto");
        }
      });
  });
}

enviarSolicitacao("alunos", document.getElementById("form-alunos"));
enviarSolicitacao("docentes", document.getElementById("form-docentes"));
