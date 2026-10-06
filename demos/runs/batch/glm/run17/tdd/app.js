function trocarAba(nome) {
  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.classList.toggle("ativa", aba.dataset.aba === nome);
  });
  document.querySelectorAll(".painel").forEach(function (painel) {
    painel.hidden = painel.id !== "aba-" + nome;
  });
}

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    trocarAba(aba.dataset.aba);
  });
});

function apenasDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(digitos) {
  if (!digitos) { return ""; }
  var centavos = digitos.slice(-2).padStart(2, "0");
  var inteiro = digitos.slice(0, -2) || "0";
  var grupos = [];
  while (inteiro.length > 3) {
    grupos.unshift(inteiro.slice(-3));
    inteiro = inteiro.slice(0, -3);
  }
  grupos.unshift(inteiro);
  return "R$ " + grupos.join(".") + "," + centavos;
}

document.querySelectorAll("[data-moeda]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    var digitos = apenasDigitos(campo.value);
    campo.value = digitos ? formatarMoeda(digitos) : "";
  });
});

document.querySelectorAll("[data-cpf]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    var d = apenasDigitos(campo.value);
    campo.value = d.length === 11
      ? d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9)
      : campo.value;
  });
});

document.querySelectorAll("[data-cep]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    var d = apenasDigitos(campo.value);
    campo.value = d.length === 8 ? d.slice(0, 5) + "-" + d.slice(5) : campo.value;
  });
});

document.querySelectorAll("[data-data]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    var d = apenasDigitos(campo.value);
    campo.value = d.length === 8 ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4) : campo.value;
  });
});

function coletarDados(form) {
  var dados = { tipo: form.id === "form-alunos" ? "alunos" : "docentes" };
  new FormData(form).forEach(function (valor, nome) {
    dados[nome] = valor;
  });
  return dados;
}

function mostrarErros(form, erros) {
  var lista = document.getElementById("erros-" + (form.id === "form-alunos" ? "alunos" : "docentes"));
  lista.innerHTML = "";
  erros.forEach(function (mensagem) {
    var item = document.createElement("li");
    item.textContent = mensagem;
    lista.appendChild(item);
  });
  lista.hidden = erros.length === 0;
}

function enviar(form) {
  fetch("/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(coletarDados(form)),
  })
    .then(function (resposta) { return resposta.json(); })
    .then(function (corpo) {
      if (corpo.oficio) {
        document.querySelector("main").hidden = true;
        document.querySelectorAll(".abas").forEach(function (n) { n.hidden = true; });
        var confirmacao = document.getElementById("confirmacao");
        document.getElementById("oficio").textContent = corpo.oficio;
        confirmacao.hidden = false;
      } else {
        mostrarErros(form, corpo.erros || []);
      }
    });
}

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    enviar(form);
  });
});
