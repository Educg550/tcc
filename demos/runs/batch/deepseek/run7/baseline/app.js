(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  for (var i = 0; i < abas.length; i++) {
    abas[i].addEventListener("click", function () {
      for (var j = 0; j < abas.length; j++) {
        abas[j].classList.remove("ativa");
      }
      this.classList.add("ativa");
      var aba = this.dataset.aba;
      document.getElementById("painel-alunos").classList.toggle("escondido", aba !== "alunos");
      document.getElementById("painel-docentes").classList.toggle("escondido", aba !== "docentes");
    });
  }

  function soDigitos(v) {
    return v.replace(/\D/g, "");
  }

  function formataValor(v) {
    var d = soDigitos(v);
    if (!d) return "";
    d = d.replace(/^0+/, "") || "0";
    while (d.length < 3) d = "0" + d;
    var centavos = d.slice(-2);
    var inteiros = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + inteiros + "," + centavos;
  }

  function formataCpf(v) {
    var d = soDigitos(v).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function formataCep(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formataData(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  var formatadores = {
    valor: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data_nascimento: formataData
  };

  var campos = document.querySelectorAll("input");
  for (var k = 0; k < campos.length; k++) {
    (function (campo) {
      var f = formatadores[campo.name];
      if (!f) return;
      campo.addEventListener("blur", function () {
        campo.value = f(campo.value);
      });
    })(campos[k]);
  }

  function mostraErros(form, erros) {
    var caixa = form.querySelector(".erros");
    caixa.innerHTML = "";
    for (var i = 0; i < erros.length; i++) {
      var linha = document.createElement("div");
      linha.textContent = erros[i];
      caixa.appendChild(linha);
    }
    caixa.classList.remove("escondido");
  }

  function mostraConfirmacao(oficio) {
    document.getElementById("abas").classList.add("escondido");
    document.getElementById("painel-alunos").classList.add("escondido");
    document.getElementById("painel-docentes").classList.add("escondido");
    document.getElementById("oficio").textContent = oficio;
    document.getElementById("confirmacao").classList.remove("escondido");
  }

  var formularios = document.querySelectorAll("form");
  for (var n = 0; n < formularios.length; n++) {
    (function (form) {
      form.addEventListener("submit", function (evento) {
        evento.preventDefault();
        var dados = {};
        var fd = new FormData(form);
        fd.forEach(function (valor, chave) {
          dados[chave] = valor;
        });
        dados.aba = form.id === "form-alunos" ? "alunos" : "docentes";

        fetch("/api/solicitar", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dados)
        })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (res.erros && res.erros.length) {
              mostraErros(form, res.erros);
              return;
            }
            mostraConfirmacao(res.oficio);
          });
      });
    })(formularios[n]);
  }
})();
