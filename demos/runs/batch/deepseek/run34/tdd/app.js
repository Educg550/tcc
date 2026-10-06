(function () {
  function soDigitos(v) {
    return (v || "").replace(/\D/g, "");
  }

  function comMilhar(s) {
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function formatarValor(v) {
    var d = soDigitos(v);
    if (!d) return "";
    var n = parseInt(d, 10);
    var reais = Math.floor(n / 100);
    var cent = n % 100;
    return "R$ " + comMilhar(String(reais)) + "," + String(cent).padStart(2, "0");
  }

  function formatarCPF(v) {
    var d = soDigitos(v).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  function formatarCEP(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formatarData(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var FORMATADORES = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData
  };

  document.querySelectorAll("input").forEach(function (campo) {
    var formatador = FORMATADORES[campo.name];
    if (formatador) {
      campo.addEventListener("blur", function () {
        campo.value = formatador(campo.value);
      });
    }
  });

  var abas = document.querySelectorAll(".aba");
  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (b) { b.classList.remove("ativa"); });
      aba.classList.add("ativa");
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.classList.toggle("ativo", painel.dataset.aba === aba.dataset.aba);
      });
    });
  });

  document.querySelectorAll("form.formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var aba = form.dataset.aba;
      var dados = { aba: aba };
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = valor;
      });
      var caixa = document.getElementById("erros-" + aba);
      caixa.replaceChildren();

      fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (json) {
          var lista = json.erros || [];
          if (lista.length) {
            lista.forEach(function (mensagem) {
              var p = document.createElement("p");
              p.textContent = mensagem;
              caixa.appendChild(p);
            });
            return;
          }
          document.querySelectorAll(".painel").forEach(function (painel) {
            painel.classList.remove("ativo");
          });
          document.querySelector(".abas").style.display = "none";
          document.getElementById("confirmacao").hidden = false;
          document.getElementById("oficio").textContent = json.oficio || "";
        });
    });
  });
})();
