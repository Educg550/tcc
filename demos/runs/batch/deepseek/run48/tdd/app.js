(function () {
  "use strict";

  var abas = document.querySelectorAll(".aba");
  var formularios = document.querySelectorAll(".formulario");

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.remove("ativa");
      });
      aba.classList.add("ativa");
      formularios.forEach(function (formulario) {
        formulario.hidden = formulario.dataset.aba !== aba.dataset.aba;
      });
    });
  });

  function formatarMoeda(campo) {
    var digitos = campo.value.replace(/\D/g, "");
    if (!digitos) {
      campo.value = "";
      return;
    }
    var centavos = parseInt(digitos, 10);
    var reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    campo.value = "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
  }

  function formatarCPF(campo) {
    var digitos = campo.value.replace(/\D/g, "").slice(0, 11);
    if (digitos.length > 9) {
      digitos = digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, "$1.$2.$3-$4");
    } else if (digitos.length > 6) {
      digitos = digitos.replace(/(\d{3})(\d{3})(\d{1,3})/, "$1.$2.$3");
    } else if (digitos.length > 3) {
      digitos = digitos.replace(/(\d{3})(\d{1,3})/, "$1.$2");
    }
    campo.value = digitos;
  }

  function formatarCEP(campo) {
    var digitos = campo.value.replace(/\D/g, "").slice(0, 8);
    if (digitos.length > 5) {
      digitos = digitos.replace(/(\d{5})(\d{1,3})/, "$1-$2");
    }
    campo.value = digitos;
  }

  function formatarData(campo) {
    var digitos = campo.value.replace(/\D/g, "").slice(0, 8);
    if (digitos.length > 4) {
      digitos = digitos.replace(/(\d{2})(\d{2})(\d{1,4})/, "$1/$2/$3");
    } else if (digitos.length > 2) {
      digitos = digitos.replace(/(\d{2})(\d{1,2})/, "$1/$2");
    }
    campo.value = digitos;
  }

  [
    [".formata-moeda", formatarMoeda],
    [".formata-cpf", formatarCPF],
    [".formata-cep", formatarCEP],
    [".formata-data", formatarData]
  ].forEach(function (par) {
    document.querySelectorAll(par[0]).forEach(function (campo) {
      campo.addEventListener("blur", function () {
        par[1](campo);
      });
    });
  });

  formularios.forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();

      var dados = {};
      formulario.querySelectorAll("[name]").forEach(function (campo) {
        dados[campo.name] = campo.value.trim();
      });

      fetch("/api/solicitacao/" + formulario.dataset.aba, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          var areaErros = formulario.querySelector(".erros");
          if (resultado.erros && resultado.erros.length) {
            areaErros.textContent = resultado.erros.join("\n");
            areaErros.hidden = false;
            return;
          }
          areaErros.hidden = true;
          document.getElementById("painel-formularios").hidden = true;
          document.getElementById("oficio").textContent = resultado.oficio;
          document.getElementById("painel-confirmacao").hidden = false;
        });
    });
  });
})();
