(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var abasPainel = {
    alunos: document.getElementById("painel-alunos"),
    docentes: document.getElementById("painel-docentes"),
  };
  var confirmacao = document.getElementById("confirmacao");
  var principal = document.getElementById("principal");

  function mostrarAba(nome) {
    abas.forEach(function (a) {
      var ativa = a.dataset.aba === nome;
      a.classList.toggle("ativa", ativa);
      a.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    Object.keys(abasPainel).forEach(function (k) {
      abasPainel[k].hidden = k !== nome;
    });
    confirmacao.hidden = true;
    var form = abasPainel[nome] ? abasPainel[nome].querySelector("form") : null;
    principal.insertBefore(form ? form.parentElement : principal.firstChild, abasPainel.alunos);
    abasPainel.alunos.style.order = nome === "alunos" ? "1" : "2";
    abasPainel.docentes.style.order = nome === "docentes" ? "1" : "2";
  }

  abas.forEach(function (a) {
    a.addEventListener("click", function () { mostrarAba(a.dataset.aba); });
  });

  function somenteDigitos(v) { return (v || "").replace(/\D/g, ""); }

  function moedaBr(digitos) {
    if (!digitos) return "R$ 0,00";
    var d = parseInt(digitos, 10);
    var inteiro = Math.floor(d / 100);
    var cent = d % 100;
    var centStr = (cent < 10 ? "0" : "") + cent;
    var grupo = inteiro % 1000, resto = Math.floor(inteiro / 1000);
    var partes = [];
    while (grupo >= 1000) {
      partes.push(("00" + (grupo % 1000)).slice(-3));
      grupo = Math.floor(grupo / 1000);
    }
    partes.push(String(grupo));
    return "R$ " + partes.reverse().join(".") + "," + centStr;
  }

  function formatCpf(v) {
    var d = somenteDigitos(v);
    var out = d.slice(0, 3);
    if (d.length > 3) out += "." + d.slice(3, 6);
    if (d.length > 6) out += "." + d.slice(6, 9);
    if (d.length > 9) out += "-" + d.slice(9, 11);
    return out;
  }

  function formatCep(v) {
    var d = somenteDigitos(v);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5, 8);
    return d;
  }

  function formatData(v) {
    var d = somenteDigitos(v);
    var out = d.slice(0, 2);
    if (d.length > 2) out += "/" + d.slice(2, 4);
    if (d.length > 4) out += "/" + d.slice(4, 8);
    return out;
  }

  function formatValor(v) {
    return moedaBr(somenteDigitos(v));
  }

  var formatadores = {
    valor: formatValor,
    cpf: formatCpf,
    cep: formatCep,
    nascimento: formatData,
  };

  document.querySelectorAll(".form").forEach(function (form) {
    Object.keys(formatadores).forEach(function (nome) {
      var inp = form.querySelector('[name="' + nome + '"]');
      if (inp) inp.addEventListener("blur", function () { inp.value = formatadores[nome](inp.value); });
    });

    var tipo = form.dataset.tipo;
    var errosDiv = document.getElementById("erros-" + tipo);

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      errosDiv.hidden = true;
      errosDiv.innerHTML = "";
      confirmacao.hidden = true;

      var payload = { tipo: tipo };
      form.querySelectorAll("input, select, textarea").forEach(function (el) {
        payload[el.name] = el.value;
      });

      fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            abasPainel.alunos.hidden = true;
            abasPainel.docentes.hidden = true;
            document.getElementById("oficio").textContent = data.oficio;
            confirmacao.hidden = false;
          } else {
            (data.erros || []).forEach(function (m) {
              var p = document.createElement("p");
              p.textContent = m;
              errosDiv.appendChild(p);
            });
            errosDiv.hidden = false;
          }
        })
        .catch(function () {
          var p = document.createElement("p");
          p.textContent = "N\u00e3o foi poss\u00edvel enviar a solicita\u00e7\u00e3o.";
          errosDiv.appendChild(p);
          errosDiv.hidden = false;
        });
    });
  });
})();
