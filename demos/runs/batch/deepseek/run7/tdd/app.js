(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var formAlunos = document.getElementById("form-alunos");
  var formDocentes = document.getElementById("form-docentes");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (a) { a.classList.toggle("ativa", a === aba); });
      var nome = aba.dataset.aba;
      formAlunos.classList.toggle("ativa", nome === "ALUNOS");
      formDocentes.classList.toggle("ativa", nome === "DOCENTES");
    });
  });

  function formatarMoeda(valor) {
    var digitos = valor.replace(/\D/g, "");
    if (!digitos) return "";
    digitos = digitos.replace(/^0+/, "") || "0";
    while (digitos.length < 3) digitos = "0" + digitos;
    var centavos = digitos.slice(-2);
    var inteiros = digitos.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + inteiros + "," + centavos;
  }

  function formatarCPF(valor) {
    var d = valor.replace(/\D/g, "").slice(0, 11);
    return d
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d{1,2})$/, ".$1-$2");
  }

  function formatarCEP(valor) {
    var d = valor.replace(/\D/g, "").slice(0, 8);
    return d.replace(/^(\d{5})(\d)/, "$1-$2");
  }

  function formatarData(valor) {
    var d = valor.replace(/\D/g, "").slice(0, 8);
    return d
      .replace(/^(\d{2})(\d)/, "$1/$2")
      .replace(/^(\d{2})\/(\d{2})(\d)/, "$1/$2/$3");
  }

  var formatadores = {
    moeda: formatarMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data: formatarData
  };

  document.querySelectorAll("[data-formato]").forEach(function (input) {
    input.addEventListener("blur", function () {
      input.value = formatadores[input.dataset.formato](input.value);
    });
  });

  function enviar(form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = {};
      new FormData(form).forEach(function (valor, chave) {
        dados[chave] = typeof valor === "string" ? valor.trim() : valor;
      });
      dados.aba = form.dataset.aba;

      fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json().then(function (corpo) {
            return { status: resposta.status, corpo: corpo };
          });
        })
        .then(function (resultado) {
          var erros = form.querySelector(".erros");
          if (resultado.status !== 200) {
            erros.innerHTML = (resultado.corpo.errors || [])
              .map(function (msg) {
                var p = document.createElement("div");
                p.textContent = msg;
                return p.outerHTML;
              })
              .join("<br>");
            return;
          }
          erros.textContent = "";
          document.getElementById("oficio").textContent = resultado.corpo.oficio;
          document.getElementById("pagina-formulario").classList.add("oculto");
          document.getElementById("pagina-confirmacao").classList.remove("oculto");
        });
    });
  }

  enviar(formAlunos);
  enviar(formDocentes);
})();
