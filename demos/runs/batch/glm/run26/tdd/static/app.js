function mostrarAba(nome) {
  document.querySelectorAll(".aba").forEach(function (b) {
    b.classList.toggle("ativa", b.dataset.aba === nome);
  });
  document.querySelectorAll(".painel").forEach(function (p) {
    var ativo = p.id === nome;
    p.classList.toggle("ativo", ativo);
    p.hidden = !ativo;
  });
}

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    mostrarAba(botao.dataset.aba);
  });
});

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(digitos) {
  var limpos = soDigitos(digitos);
  if (!limpos) return "";
  var centavos = parseInt(limpos, 10);
  var reais = Math.floor(centavos / 100);
  var cent = (centavos % 100).toString().padStart(2, "0");
  var partes = [];
  while (reais >= 1000) {
    partes.unshift(String(reais % 1000).padStart(3, "0"));
    reais = Math.floor(reais / 1000);
  }
  partes.unshift(String(reais));
  return "R$ " + partes.join(".") + "," + cent;
}

function formatarCpf(digitos) {
  var d = soDigitos(digitos).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function formatarCep(digitos) {
  var d = soDigitos(digitos).slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formatarData(digitos) {
  var d = soDigitos(digitos).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

var formatos = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

document.querySelectorAll("[data-formato]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    var fn = formatos[campo.dataset.formato];
    if (fn && campo.value) campo.value = fn(campo.value);
  });
});

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var errosDiv = form.parentElement.querySelector(".erros");
    errosDiv.hidden = true;
    errosDiv.textContent = "";
    var dados = { aba: form.dataset.aba };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = valor;
    });
    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    })
      .then(function (resp) { return resp.json(); })
      .then(function (resposta) {
        if (!resposta.ok) {
          errosDiv.textContent = resposta.erros.join("\n");
          errosDiv.hidden = false;
          return;
        }
        document.querySelector("main").hidden = true;
        var confirmacao = document.getElementById("confirmacao");
        document.getElementById("oficio").textContent = resposta.oficio;
        confirmacao.hidden = false;
      });
  });
});
