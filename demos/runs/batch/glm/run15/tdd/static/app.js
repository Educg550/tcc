(function () {
  "use strict";

  var tabAlunos = document.getElementById("tab-alunos");
  var tabDocentes = document.getElementById("tab-docentes");
  var secAlunos = document.getElementById("form-alunos-section");
  var secDocentes = document.getElementById("form-docentes-section");

  function ativarAba(alunos) {
    secAlunos.hidden = !alunos;
    secDocentes.hidden = alunos;
    tabAlunos.classList.toggle("active", alunos);
    tabDocentes.classList.toggle("active", !alunos);
  }

  tabAlunos.addEventListener("click", function () {
    ativarAba(true);
  });

  tabDocentes.addEventListener("click", function () {
    ativarAba(false);
  });

  function mostrarErros(ul, erros) {
    ul.textContent = "";
    erros.forEach(function (msg) {
      var li = document.createElement("li");
      li.textContent = msg;
      ul.appendChild(li);
    });
  }

  function enviarFormulario(form, ulErros) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      fetch(form.action, {
        method: form.method,
        body: new FormData(form)
      }).then(function (response) {
        return response.json();
      }).then(function (data) {
        if (!data.ok) {
          mostrarErros(ulErros, data.erros);
          return;
        }
        var confirmation = document.getElementById("confirmation");
        var oficio = document.getElementById("oficio");
        oficio.textContent = data.oficio;
        confirmation.hidden = false;
        form.parentElement.hidden = true;
        var tabs = document.querySelector(".tabs");
        if (tabs) {
          tabs.hidden = true;
        }
      }).catch(function () {
        mostrarErros(ulErros, ["Não foi possível enviar a solicitação."]);
      });
    });
  }

  enviarFormulario(
    document.getElementById("form-alunos"),
    document.getElementById("errors-alunos")
  );
  enviarFormulario(
    document.getElementById("form-docentes"),
    document.getElementById("errors-docentes")
  );

  function montarMascara(input, aplicar) {
    input.addEventListener("input", function () {
      var digitos = input.value.replace(/\D/g, "").slice(0, aplicar.length);
      input.value = digitos;
    });
    input.addEventListener("blur", function () {
      var digitos = input.value.replace(/\D/g, "").slice(0, aplicar.length);
      if (digitos.length === aplicar.length) {
        input.value = aplicar(digitos);
      }
    });
  }

  function formatarCpf(d) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9, 11);
  }

  function formatarCep(d) {
    return d.slice(0, 5) + "-" + d.slice(5, 8);
  }

  function formatarData(d) {
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4, 8);
  }

  function formatarValor(d) {
    var centavos = d;
    var inteiro = centavos.slice(0, -2);
    var decimal = centavos.slice(-2);
    if (inteiro === "") {
      inteiro = "0";
    }
    var grupos = [];
    while (inteiro.length > 3) {
      grupos.unshift(inteiro.slice(-3));
      inteiro = inteiro.slice(0, -3);
    }
    grupos.unshift(inteiro);
    return "R$ " + grupos.join(".") + "," + decimal;
  }

  function mascaraPorId(id, aplicar, maxDigitos) {
    var input = document.getElementById(id);
    if (!input) {
      return;
    }
    input.addEventListener("input", function () {
      var digitos = input.value.replace(/\D/g, "").slice(0, maxDigitos);
      input.value = digitos;
    });
    input.addEventListener("blur", function () {
      var digitos = input.value.replace(/\D/g, "").slice(0, maxDigitos);
      if (digitos.length === maxDigitos) {
        input.value = aplicar(digitos);
      }
    });
  }

  ["valor", "valor-docentes"].forEach(function (id) {
    mascaraPorId(id, formatarValor, 15);
  });
  ["cpf", "cpf-docentes"].forEach(function (id) {
    mascaraPorId(id, formatarCpf, 11);
  });
  ["cep", "cep-docentes"].forEach(function (id) {
    mascaraPorId(id, formatarCep, 8);
  });
  ["nascimento", "nascimento-docentes"].forEach(function (id) {
    mascaraPorId(id, formatarData, 8);
  });
  ["nusp", "nusp-docentes", "agencia", "agencia-docentes"].forEach(function (id) {
    mascaraPorId(id, String, 15);
  });
})();
