function abaAtiva() {
  return document.querySelector(".aba.ativa").dataset.aba;
}

document.querySelectorAll(".aba").forEach(function (botao) {
  botao.addEventListener("click", function () {
    document.querySelectorAll(".aba").forEach(function (b) { b.classList.remove("ativa"); });
    botao.classList.add("ativa");
    document.getElementById("form-alunos").hidden = botao.dataset.aba !== "alunos";
    document.getElementById("form-docentes").hidden = botao.dataset.aba !== "docentes";
  });
});

function apenasDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

function formatarMoeda(digitos) {
  var d = apenasDigitos(digitos);
  if (!d) return "";
  var centavos = parseInt(d, 10);
  var inteiro = Math.floor(centavos / 100).toString();
  var cent = String(centavos % 100).padStart(2, "0");
  var grupos = [];
  while (inteiro.length > 3) {
    grupos.unshift(inteiro.slice(-3));
    inteiro = inteiro.slice(0, -3);
  }
  grupos.unshift(inteiro);
  return "R$ " + grupos.join(".") + "," + cent;
}

function formatarCpf(digitos) {
  var d = apenasDigitos(digitos).slice(0, 11);
  if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
  return d;
}

function formatarCep(digitos) {
  var d = apenasDigitos(digitos).slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formatarData(digitos) {
  var d = apenasDigitos(digitos).slice(0, 8);
  if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
  return d;
}

document.querySelectorAll("form").forEach(function (form) {
  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var dados = { aba: abaAtiva() };
    new FormData(form).forEach(function (valor, chave) { dados[chave] = valor; });
    fetch("/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    }).then(function (r) { return r.json(); }).then(function (corpo) {
      var campoErros = form.querySelector(".erros");
      if (corpo.valido) {
        document.querySelector(".abas").hidden = true;
        form.hidden = true;
        document.getElementById("oficio").textContent = corpo.oficio;
        document.getElementById("confirmacao").hidden = false;
        campoErros.style.display = "none";
        campoErros.textContent = "";
        return;
      }
      (corpo.dados || {}).entries && Object.entries(corpo.dados).forEach(function (par) {
        var campo = form.elements[par[0]];
        if (campo) campo.value = par[1];
      });
      campoErros.textContent = (corpo.erros || []).join("\n");
      campoErros.style.display = "block";
    });
  });

  form.querySelector("[name=valor]").addEventListener("blur", function () {
    this.value = formatarMoeda(this.value);
  });
  form.querySelector("[name=cpf]").addEventListener("blur", function () {
    this.value = formatarCpf(this.value);
  });
  form.querySelector("[name=cep]").addEventListener("blur", function () {
    this.value = formatarCep(this.value);
  });
  form.querySelector("[name=nascimento]").addEventListener("blur", function () {
    this.value = formatarData(this.value);
  });
});

document.getElementById("voltar").addEventListener("click", function () {
  document.getElementById("confirmacao").hidden = true;
  document.querySelector(".abas").hidden = false;
  document.getElementById("form-" + abaAtiva()).hidden = false;
});
