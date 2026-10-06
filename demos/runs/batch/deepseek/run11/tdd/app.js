(function () {
  "use strict";

  var FORMATADORES = {
    "VALOR SOLICITADO (R$)": function (v) {
      var d = v.replace(/\D/g, "");
      if (!d) return "";
      var centavos = parseInt(d, 10);
      var reais = Math.floor(centavos / 100);
      var cent = String(centavos % 100).padStart(2, "0");
      return "R$ " + String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + cent;
    },
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": function (v) {
      var d = v.replace(/\D/g, "").slice(0, 11);
      var r = d.slice(0, 3);
      if (d.length > 3) r += "." + d.slice(3, 6);
      if (d.length > 6) r += "." + d.slice(6, 9);
      if (d.length > 9) r += "-" + d.slice(9, 11);
      return r;
    },
    "CEP": function (v) {
      var d = v.replace(/\D/g, "").slice(0, 8);
      return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
    },
    "DATA DE NASCIMENTO": function (v) {
      var d = v.replace(/\D/g, "").slice(0, 8);
      var r = d.slice(0, 2);
      if (d.length > 2) r += "/" + d.slice(2, 4);
      if (d.length > 4) r += "/" + d.slice(4, 8);
      return r;
    }
  };

  document.querySelectorAll("[name]").forEach(function (campo) {
    var formatador = FORMATADORES[campo.name];
    if (formatador) {
      campo.addEventListener("blur", function () {
        campo.value = formatador(campo.value);
      });
    }
  });

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      var aba = botao.dataset.aba;
      document.querySelectorAll(".aba").forEach(function (b) {
        b.classList.toggle("ativa", b === botao);
      });
      document.querySelectorAll(".formulario").forEach(function (form) {
        var ativo = form.dataset.aba === aba;
        form.classList.toggle("ativo", ativo);
        form.hidden = !ativo;
      });
    });
  });

  function mostrarConfirmacao(oficio) {
    var conteudo = document.getElementById("conteudo");
    conteudo.innerHTML = "";
    var caixa = document.createElement("div");
    caixa.className = "confirmacao";
    var titulo = document.createElement("h2");
    titulo.textContent = "Solicitação registrada";
    var corpo = document.createElement("div");
    corpo.className = "oficio";
    corpo.textContent = oficio;
    caixa.appendChild(titulo);
    caixa.appendChild(corpo);
    conteudo.appendChild(caixa);
    window.scrollTo(0, 0);
  }

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var aba = form.dataset.aba;
      var campos = {};
      form.querySelectorAll("[name]").forEach(function (el) {
        campos[el.name] = el.value;
      });
      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aba: aba, campos: campos })
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (corpo) {
          var erros = form.querySelector(".erros");
          if (corpo.erros && corpo.erros.length) {
            erros.textContent = corpo.erros.join("\n");
            erros.hidden = false;
            window.scrollTo(0, 0);
          } else {
            erros.hidden = true;
            mostrarConfirmacao(corpo.oficio);
          }
        });
    });
  });
})();
