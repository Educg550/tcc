// Comportamento de tela: abas, formatação de campos e envio.

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("ativa"); });
    aba.classList.add("ativa");
    document.querySelectorAll(".formulario").forEach(function (f) {
      f.classList.remove("ativo");
    });
    document.getElementById(aba.dataset.aba).classList.add("ativo");
  });
});

function formatarValor(valor) {
  var digitos = valor.replace(/\D/g, "");
  if (!digitos) return "";
  var centavos = parseInt(digitos, 10);
  var inteiro = Math.floor(centavos / 100).toLocaleString("pt-BR");
  return "R$ " + inteiro + "," + String(centavos % 100).padStart(2, "0");
}

function formatarCpf(valor) {
  var d = valor.replace(/\D/g, "").slice(0, 11);
  return d.replace(/^(\d{0,3})(\d{0,3})(\d{0,3})(\d{0,2})$/, function (_, a, b, c, e) {
    return [a, b ? "." + b : "", c ? "." + c : "", e ? "-" + e : ""].join("");
  });
}

function formatarCep(valor) {
  var d = valor.replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  var d = valor.replace(/\D/g, "").slice(0, 8);
  return [d.slice(0, 2), d.slice(2, 4), d.slice(4)].filter(Boolean).join("/");
}

var formatadores = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData,
};

Object.keys(formatadores).forEach(function (nome) {
  document.querySelectorAll('input[name="' + nome + '"]').forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = formatadores[nome](campo.value);
    });
  });
});

function enviar(event) {
  event.preventDefault();
  var form = event.target;
  var aba = form.id === "form-alunos" ? "alunos" : "docentes";
  var dados = { tipo: aba };
  new FormData(form).forEach(function (valor, campo) {
    if (campo !== "tipo") dados[campo] = valor;
  });
  var divErros = form.querySelector(".erros");
  fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  })
    .then(function (resp) { return resp.json(); })
    .then(function (dadosResposta) {
      if (dadosResposta.erros) {
        divErros.innerHTML = dadosResposta.erros.map(function (e) { return e + "<br>"; }).join("");
        return;
      }
      document.getElementById("oficio").textContent = dadosResposta.oficio;
      document.querySelector("main").classList.add("oculto");
      document.getElementById("confirmacao").classList.remove("oculto");
    });
}

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", enviar);
});

document.getElementById("nova-solicitacao").addEventListener("click", function () {
  document.getElementById("confirmacao").classList.add("oculto");
  document.querySelector("main").classList.remove("oculto");
});
