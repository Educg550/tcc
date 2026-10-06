document.addEventListener("DOMContentLoaded", function () {
  var abas = document.querySelectorAll(".aba");
  var paineis = document.querySelectorAll(".painel[data-aba]");

  abas.forEach(function (botao) {
    botao.addEventListener("click", function () {
      abas.forEach(function (b) {
        b.classList.toggle("ativa", b === botao);
      });
      paineis.forEach(function (p) {
        p.classList.toggle("ativa", p.dataset.aba === botao.dataset.aba);
      });
    });
  });

  function apenasDigitos(texto) {
    return (texto || "").replace(/\D/g, "");
  }

  function formatarMoeda(texto) {
    var d = apenasDigitos(texto).slice(0, 15);
    if (!d) return "";
    var centavos = d.padStart(3, "0");
    var reais = centavos.slice(0, -2);
    var cent = centavos.slice(-2);
    return "R$ " + reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + cent;
  }

  function formatarCpf(texto) {
    var d = apenasDigitos(texto).slice(0, 11);
    if (d.length > 9) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, "$1.$2.$3-$4");
    if (d.length > 6) return d.replace(/(\d{3})(\d{3})(\d{0,3})/, "$1.$2.$3");
    if (d.length > 3) return d.replace(/(\d{3})(\d{0,3})/, "$1.$2");
    return d;
  }

  function formatarCep(texto) {
    var d = apenasDigitos(texto).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formatarData(texto) {
    var d = apenasDigitos(texto).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var mascaras = {
    "VALOR SOLICITADO (R$)": formatarMoeda,
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": formatarCpf,
    "CEP": formatarCep,
    "DATA DE NASCIMENTO": formatarData
  };

  document.querySelectorAll("input[name]").forEach(function (campo) {
    var fn = mascaras[campo.name];
    if (fn) {
      campo.addEventListener("blur", function () {
        campo.value = fn(campo.value);
      });
    }
  });

  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = Object.fromEntries(new FormData(form).entries());
      dados.aba = form.dataset.aba;

      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (corpo) {
          var area = form.querySelector(".erros");
          if (corpo.erros && corpo.erros.length) {
            area.innerHTML = corpo.erros.map(function (msg) {
              return "<p>" + msg + "</p>";
            }).join("");
            return;
          }
          area.innerHTML = "";
          document.getElementById("oficio").textContent = corpo.oficio;
          document.querySelectorAll(".painel").forEach(function (p) {
            p.classList.remove("ativa");
          });
          document.getElementById("confirmacao").classList.add("ativa");
        });
    });
  });
});
