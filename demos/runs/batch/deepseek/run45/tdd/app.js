(function () {
  "use strict";

  var abas = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  var paineis = Array.prototype.slice.call(document.querySelectorAll(".tab-panel"));

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.remove("active");
        outra.setAttribute("aria-selected", "false");
      });
      paineis.forEach(function (painel) {
        painel.classList.remove("active");
      });
      aba.classList.add("active");
      aba.setAttribute("aria-selected", "true");
      document.getElementById(aba.dataset.panel).classList.add("active");
    });
  });

  function apenasDigitos(valor) {
    return (valor || "").replace(/\D/g, "");
  }

  function formatarMoeda(valor) {
    var digitos = apenasDigitos(valor);
    if (!digitos) return "";
    digitos = digitos.replace(/^0+(?=\d)/, "").padStart(3, "0");
    var centavos = digitos.slice(-2);
    var reais = digitos.slice(0, -2).replace(/^0+/, "") || "0";
    reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formatarCPF(valor) {
    var d = apenasDigitos(valor).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  function formatarCEP(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formatarData(valor) {
    var d = apenasDigitos(valor).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var formatadores = {
    moeda: formatarMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data: formatarData
  };

  Array.prototype.slice.call(document.querySelectorAll("[data-format]")).forEach(function (campo) {
    var formatar = formatadores[campo.dataset.format];
    if (!formatar) return;
    campo.addEventListener("blur", function () {
      campo.value = formatar(campo.value);
    });
  });

  Array.prototype.slice.call(document.querySelectorAll(".formulario")).forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var caixaErros = formulario.querySelector(".erros");
      caixaErros.innerHTML = "";
      fetch(formulario.action, { method: "POST", body: new FormData(formulario) })
        .then(function (resposta) {
          return resposta.text();
        })
        .then(function (html) {
          if (html.trim().indexOf("<section") === 0) {
            document.querySelector("main").innerHTML = html;
          } else {
            caixaErros.innerHTML = html;
          }
        });
    });
  });
})();
