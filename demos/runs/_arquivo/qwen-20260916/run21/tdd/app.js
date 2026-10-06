document.addEventListener("DOMContentLoaded", function () {
  var abas = document.querySelectorAll(".aba");
  var forms = document.querySelectorAll(".form-aba");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      var alvo = aba.getAttribute("data-aba");
      abas.forEach(function (a) { a.classList.remove("ativa"); });
      aba.classList.add("ativa");
      forms.forEach(function (f) {
        f.classList.add("oculto");
        if (f.getAttribute("data-aba") === alvo) {
          f.classList.remove("oculto");
        }
      });
    });
  });

  document.querySelectorAll("input.moeda").forEach(function (input) {
    input.addEventListener("blur", function () {
      var digits = input.value.replace(/\D/g, "");
      if (digits.length === 0) { input.value = ""; return; }
      var cents = parseInt(digits, 10);
      var inteiro = Math.floor(cents / 100);
      var centavos = cents % 100;
      var formatted = inteiro.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      input.value = "R$ " + formatted + "," + (centavos < 10 ? "0" : "") + centavos;
    });
  });

  document.querySelectorAll("input.cpf").forEach(function (input) {
    input.addEventListener("blur", function () {
      var digits = input.value.replace(/\D/g, "").substring(0, 11);
      if (digits.length === 0) { input.value = ""; return; }
      var result = "";
      for (var i = 0; i < digits.length; i++) {
        result += digits[i];
        if (i === 2) result += ".";
        if (i === 5) result += ".";
        if (i === 8) result += "-";
      }
      input.value = result;
    });
  });

  document.querySelectorAll("input.cep").forEach(function (input) {
    input.addEventListener("blur", function () {
      var digits = input.value.replace(/\D/g, "").substring(0, 8);
      if (digits.length === 0) { input.value = ""; return; }
      var result = digits.substring(0, 5);
      if (digits.length > 5) result += "-" + digits.substring(5);
      input.value = result;
    });
  });

  document.querySelectorAll("input.data").forEach(function (input) {
    input.addEventListener("blur", function () {
      var digits = input.value.replace(/\D/g, "").substring(0, 8);
      if (digits.length === 0) { input.value = ""; return; }
      var result = digits.substring(0, 2);
      if (digits.length > 2) result += "/" + digits.substring(2, 4);
      if (digits.length > 4) result += "/" + digits.substring(4);
      input.value = result;
    });
  });

  function getValor(input) {
    var digits = input.value.replace(/\D/g, "");
    return digits ? parseInt(digits, 10) : 0;
  }

  forms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var aba = form.getAttribute("data-aba");
      var dados = {};
      var inputs = form.querySelectorAll("input, select, textarea");
      inputs.forEach(function (input) {
        var name = input.getAttribute("name");
        if (name === "valor") {
          dados[name] = getValor(input);
        } else {
          dados[name] = input.value;
        }
      });
      dados["aba"] = aba;

      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          var box = document.getElementById("erros-" + aba);
          box.textContent = "";
          if (res.erros && res.erros.length > 0) {
            res.erros.forEach(function (erro) {
              box.textContent += erro + "\n";
            });
            return;
          }
          if (res.oficio) {
            document.getElementById("tela-form").classList.add("oculto");
            var telaConf = document.getElementById("tela-confirmacao");
            telaConf.classList.remove("oculto");
            document.getElementById("oficio").textContent = res.oficio;
          }
        });
    });
  });

  document.getElementById("btn-voltar").addEventListener("click", function () {
    var telaConf = document.getElementById("tela-confirmacao");
    var telaForm = document.getElementById("tela-form");
    telaConf.classList.add("oculto");
    telaForm.classList.remove("oculto");
  });
});
