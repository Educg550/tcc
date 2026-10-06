(function () {
  "use strict";

  function soDigitos(valor) {
    var s = valor == null ? "" : String(valor);
    var out = "";
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 48 && c <= 57) out += s.charAt(i);
    }
    return out;
  }

  function formatarValor(el) {
    var d = soDigitos(el.value);
    if (!d) { el.value = ""; return; }
    var n = parseInt(d, 10);
    var reais = Math.floor(n / 100).toLocaleString("pt-BR");
    var centavos = String(n % 100).padStart(2, "0");
    el.value = "R$ " + reais + "," + centavos;
  }

  function formatarCPF(el) {
    var d = soDigitos(el.value).slice(0, 11);
    var out = "";
    for (var i = 0; i < d.length; i++) {
      if (i === 3 || i === 6) out += ".";
      if (i === 9) out += "-";
      out += d.charAt(i);
    }
    el.value = out;
  }

  function formatarCEP(el) {
    var d = soDigitos(el.value).slice(0, 8);
    el.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(el) {
    var d = soDigitos(el.value).slice(0, 8);
    var out = "";
    for (var i = 0; i < d.length; i++) {
      if (i === 2 || i === 4) out += "/";
      out += d.charAt(i);
    }
    el.value = out;
  }

  var FORMATADORES = {
    valor: formatarValor,
    cpf: formatarCPF,
    cep: formatarCEP,
    data: formatarData
  };

  document.querySelectorAll("[data-formato]").forEach(function (el) {
    var formatar = FORMATADORES[el.dataset.formato];
    if (formatar) {
      el.addEventListener("blur", function () { formatar(el); });
    }
  });

  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (b) {
        b.classList.remove("ativa");
        b.setAttribute("aria-selected", "false");
      });
      aba.classList.add("ativa");
      aba.setAttribute("aria-selected", "true");
      document.querySelectorAll(".formulario").forEach(function (f) { f.hidden = true; });
      document.getElementById("form-" + aba.dataset.aba).hidden = false;
    });
  });

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (el.name) dados[el.name] = el.value;
      });

      var caixaErros = form.querySelector(".erros");

      fetch("/api/solicitacao/" + form.dataset.aba, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (json) {
          if (json.valido) {
            document.getElementById("conteudo").hidden = true;
            var confirmacao = document.getElementById("confirmacao");
            confirmacao.querySelector(".oficio").textContent = json.oficio;
            confirmacao.hidden = false;
          } else {
            caixaErros.textContent = "";
            json.mensagens.forEach(function (mensagem) {
              var p = document.createElement("p");
              p.textContent = mensagem;
              caixaErros.appendChild(p);
            });
            caixaErros.hidden = false;
          }
        });
    });
  });
})();
