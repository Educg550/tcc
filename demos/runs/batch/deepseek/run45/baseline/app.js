(function () {
  "use strict";

  function aplicarAba(nome) {
    document.querySelectorAll(".aba").forEach(function (b) {
      b.classList.toggle("ativa", b.dataset.aba === nome);
    });
    document.querySelectorAll(".formulario").forEach(function (f) {
      f.classList.toggle("ativo", f.dataset.form === nome);
    });
  }

  document.querySelectorAll(".aba").forEach(function (btn) {
    btn.addEventListener("click", function () {
      aplicarAba(btn.dataset.aba);
    });
  });

  function soDigitos(v) {
    return (v || "").replace(/\D/g, "");
  }

  function formataValor(v) {
    var d = soDigitos(v);
    if (!d) return "";
    var n = parseInt(d, 10);
    var reais = Math.floor(n / 100);
    var cent = n % 100;
    var s = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + s + "," + (cent < 10 ? "0" + cent : cent);
  }

  function formataCPF(v) {
    var d = soDigitos(v).slice(0, 11);
    var out = d;
    if (d.length > 3) out = d.slice(0, 3) + "." + d.slice(3);
    if (d.length > 6) out = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 9) out = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    return out;
  }

  function formataCEP(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  function formataData(v) {
    var d = soDigitos(v).slice(0, 8);
    var out = d;
    if (d.length > 2) out = d.slice(0, 2) + "/" + d.slice(2);
    if (d.length > 4) out = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    return out;
  }

  var formatadores = {
    valor: formataValor,
    cpf: formataCPF,
    cep: formataCEP,
    data: formataData
  };

  document.querySelectorAll("input[data-mask]").forEach(function (input) {
    input.addEventListener("blur", function () {
      var fn = formatadores[input.dataset.mask];
      if (fn) input.value = fn(input.value);
    });
  });

  function coletar(form) {
    var dados = { tipo_formulario: form.dataset.form };
    form.querySelectorAll("input, select, textarea").forEach(function (el) {
      if (el.name) dados[el.name] = el.value;
    });
    return dados;
  }

  function mostrarErros(form, erros) {
    var box = form.querySelector(".erros");
    if (erros && erros.length) {
      box.textContent = erros.join("\n");
      box.hidden = false;
    } else {
      box.textContent = "";
      box.hidden = true;
    }
  }

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var dados = coletar(form);
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/solicitar", true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status < 200 || xhr.status >= 300) {
          mostrarErros(form, ["Erro ao enviar solicitação"]);
          return;
        }
        var resp = JSON.parse(xhr.responseText);
        if (!resp.ok) {
          mostrarErros(form, resp.erros || []);
          return;
        }
        mostrarErros(form, []);
        document.getElementById("tela-formulario").hidden = true;
        document.getElementById("tela-confirmacao").hidden = false;
        document.getElementById("oficio").textContent = resp.oficio;
      };
      xhr.send(JSON.stringify(dados));
    });
  });
})();
