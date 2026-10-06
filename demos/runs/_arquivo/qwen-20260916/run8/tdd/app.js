(function () {
  "use strict";

  // ── Máscaras: o usuário digita só dígitos, a pontuação é da aplicação ──

  function somenteDigitos(v) {
    return v.replace(/\D/g, "");
  }

  // VALOR SOLICITADO: os dígitos são centavos -> R$ 1.500,00 (ponto milhar, vírgula centavos)
  // Ex.: 1500 -> R$ 15,00 | 150000 -> R$ 1.500,00 | 150000000 -> R$ 1.500.000,00
  function formatarValor(v) {
    var centavos = somenteDigitos(v);
    if (!centavos) return "";
    var n = BigInt(centavos);
    var inteiro = n / 100n;
    var fracao = String(Number(n % 100n)).padStart(2, "0");
    var s = String(inteiro);
    var grupos = [];
    while (s.length > 3) {
      grupos.unshift(s.slice(-3));
      s = s.slice(0, -3);
    }
    grupos.unshift(s);
    return "R$ " + grupos.join(".") + "," + fracao;
  }

  // CPF: 12345678909 -> 123.456.789-09
  function formatarCPF(v) {
    var d = somenteDigitos(v).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + "." + d.slice(3);
    return d;
  }

  // CEP: 05508090 -> 05508-090
  function formatarCEP(v) {
    var d = somenteDigitos(v).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
    return d;
  }

  // DATA DE NASCIMENTO: 01021980 -> 01/02/1980
  function formatarData(v) {
    var d = somenteDigitos(v).slice(0, 8);
    if (d.length > 6) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 4) return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + "/" + d.slice(2);
    return d;
  }

  var FORMATOS = {
    "fmt-valor": formatarValor,
    "fmt-cpf": formatarCPF,
    "fmt-cep": formatarCEP,
    "fmt-data": formatarData
  };

  // Reformatar ao sair do campo (blur), sem enviar o formulário.
  document.addEventListener("blur", function (e) {
    var el = e.target;
    if (!el.classList) return;
    for (var cls in FORMATOS) {
      if (el.classList.contains(cls)) {
        el.value = FORMATOS[cls](el.value);
        break;
      }
    }
  }, true);

  // ── Troca de abas ──

  var nav = document.querySelector(".aba-nav");
  var botoes = nav.querySelectorAll(".aba-btn");

  function mostrar(id) {
    document.querySelectorAll(".painel").forEach(function (p) {
      p.classList.toggle("oculta", p.id !== id);
    });
    botoes.forEach(function (b) {
      b.classList.toggle("ativa", b.dataset.alvo === id);
    });
  }

  botoes.forEach(function (b) {
    b.addEventListener("click", function () {
      mostrar(b.dataset.alvo);
    });
  });

  // ── Coleta, envio e resposta ──

  function coletar(form) {
    var dados = {};
    form.querySelectorAll("[name]").forEach(function (el) {
      dados[el.name] = el.value.trim();
    });
    return dados;
  }

  function mostrarErros(id, erros) {
    var box = document.getElementById(id);
    box.textContent = erros.join("\n");
  }

  function enviar(formId, endpoint, idErros) {
    var form = document.getElementById(formId);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var dados = coletar(form);
      var xhr = new XMLHttpRequest();
      xhr.open("POST", endpoint, true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.onload = function () {
        var resp = {};
        try { resp = JSON.parse(xhr.responseText); } catch (err) { resp = {}; }
        if (resp.errors && resp.errors.length) {
          mostrarErros(idErros, resp.errors);
        } else {
          mostrarErros(idErros, []);
          document.getElementById("oficio").textContent = resp.oficio || "";
          mostrar("confirmacao");
        }
      };
      xhr.send(JSON.stringify(dados));
    });
  }

  enviar("form-alunos", "/alunos", "erros-alunos");
  enviar("form-docentes", "/docentes", "erros-docentes");

  document.getElementById("voltar").addEventListener("click", function () {
    var ativa = document.querySelector(".aba-btn.ativa");
    mostrar(ativa ? ativa.dataset.alvo : "alunos");
  });
})();
