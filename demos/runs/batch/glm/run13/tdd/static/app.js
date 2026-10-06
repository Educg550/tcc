// Alternância de abas, máscaras e envio ao backend sem recarregar a página.

function trocarAba(alvo) {
  document.querySelectorAll(".aba").forEach(function (b) {
    b.classList.toggle("ativa", b.dataset.aba === alvo);
  });
  document.getElementById("form-alunos").classList.toggle("visivel", alvo === "ALUNOS");
  document.getElementById("form-docentes").classList.toggle("visivel", alvo === "DOCENTES");
}

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () { trocarAba(botao.dataset.aba); });
});

trocarAba("ALUNOS");

// Máscaras: formatam no evento de saída do campo (blur).
function somenteDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function mascaraValor(campo) {
  var cents = somenteDigitos(campo.value);
  if (cents === "") { campo.value = ""; return; }
  var inteiro = (parseInt(cents, 10) / 100).toFixed(2).split(".");
  var reais = inteiro[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  campo.value = "R$ " + reais + "," + inteiro[1];
}

function mascaraCpf(campo) {
  var d = somenteDigitos(campo.value).slice(0, 11);
  if (d.length > 9) {
    campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  } else if (d.length > 6) {
    campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  } else if (d.length > 3) {
    campo.value = d.slice(0, 3) + "." + d.slice(3);
  } else {
    campo.value = d;
  }
}

function mascaraCep(campo) {
  var d = somenteDigitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function mascaraData(campo) {
  var d = somenteDigitos(campo.value).slice(0, 8);
  var saida = d.slice(0, 2);
  if (d.length > 2) saida += "/" + d.slice(2, 4);
  if (d.length > 4) saida += "/" + d.slice(4);
  campo.value = saida;
}

document.querySelectorAll('[name="valor"]').forEach(function (c) { c.addEventListener("blur", function () { mascaraValor(c); }); });
document.querySelectorAll('[name="cpf"]').forEach(function (c) { c.addEventListener("blur", function () { mascaraCpf(c); }); });
document.querySelectorAll('[name="cep"]').forEach(function (c) { c.addEventListener("blur", function () { mascaraCep(c); }); });
document.querySelectorAll('[name="data_nascimento"]').forEach(function (c) { c.addEventListener("blur", function () { mascaraData(c); }); });

// Envio dos formulários via fetch, mantendo os valores digitados.
document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var caixa = form.querySelector(".erros");
    caixa.innerHTML = "";
    caixa.classList.remove("visivel");
    fetch("/enviar", { method: "POST", body: new FormData(form) })
      .then(function (resp) { return resp.json(); })
      .then(function (dados) {
        if (!dados.ok) {
          dados.erros.forEach(function (msg) {
            var li = document.createElement("p");
            li.textContent = msg;
            caixa.appendChild(li);
          });
          caixa.classList.add("visivel");
          return;
        }
        document.querySelector("main").innerHTML =
          "<section id=\"confirmacao\"><h3>Solicitação registrada</h3><pre id=\"oficio\"></pre></section>";
        document.getElementById("oficio").textContent = dados.oficio;
      });
  });
});
