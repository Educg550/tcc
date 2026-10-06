(function () {
  "use strict";

  var formularios = {
    alunos: document.getElementById("form-alunos"),
    docentes: document.getElementById("form-docentes")
  };
  var secaoConfirmacao = document.getElementById("confirmacao");
  var areaFormularios = document.getElementById("formularios");
  var abas = Array.prototype.slice.call(document.querySelectorAll(".aba"));
  var classesMascara = ["moeda", "cpf", "cep", "data"];

  function soDigitos(valor) {
    var saida = "";
    for (var i = 0; i < valor.length; i++) {
      var caractere = valor.charAt(i);
      if (caractere >= "0" && caractere <= "9") {
        saida += caractere;
      }
    }
    return saida;
  }

  function separarMilhares(numero) {
    var texto = String(numero);
    var saida = "";
    while (texto.length > 3) {
      saida = "." + texto.substring(texto.length - 3) + saida;
      texto = texto.substring(0, texto.length - 3);
    }
    return texto + saida;
  }

  function formatarMoeda(digitos) {
    if (!digitos) {
      return "";
    }
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = centavos % 100;
    return "R$ " + separarMilhares(reais) + "," + (resto < 10 ? "0" : "") + resto;
  }

  function formatarCpf(digitos) {
    if (digitos.length <= 3) {
      return digitos;
    }
    if (digitos.length <= 6) {
      return digitos.substring(0, 3) + "." + digitos.substring(3);
    }
    if (digitos.length <= 9) {
      return digitos.substring(0, 3) + "." + digitos.substring(3, 6) + "." + digitos.substring(6);
    }
    return digitos.substring(0, 3) + "." + digitos.substring(3, 6) + "." + digitos.substring(6, 9) + "-" + digitos.substring(9, 11);
  }

  function formatarCep(digitos) {
    if (digitos.length <= 5) {
      return digitos;
    }
    return digitos.substring(0, 5) + "-" + digitos.substring(5, 8);
  }

  function formatarData(digitos) {
    if (digitos.length <= 2) {
      return digitos;
    }
    if (digitos.length <= 4) {
      return digitos.substring(0, 2) + "/" + digitos.substring(2);
    }
    return digitos.substring(0, 2) + "/" + digitos.substring(2, 4) + "/" + digitos.substring(4, 8);
  }

  function aplicarMascara(campo) {
    var digitos = soDigitos(campo.value);
    if (campo.classList.contains("moeda")) {
      campo.value = formatarMoeda(digitos);
    } else if (campo.classList.contains("cpf")) {
      campo.value = formatarCpf(digitos);
    } else if (campo.classList.contains("cep")) {
      campo.value = formatarCep(digitos);
    } else if (campo.classList.contains("data")) {
      campo.value = formatarData(digitos);
    }
  }

  classesMascara.forEach(function (classe) {
    Array.prototype.forEach.call(document.querySelectorAll("." + classe), function (campo) {
      campo.addEventListener("blur", function () {
        aplicarMascara(campo);
      });
    });
  });

  function mostrarAba(perfil) {
    abas.forEach(function (aba) {
      var ativa = aba.getAttribute("data-perfil") === perfil;
      aba.classList.toggle("ativa", ativa);
      aba.setAttribute("aria-selected", ativa ? "true" : "false");
    });
    Object.keys(formularios).forEach(function (nome) {
      formularios[nome].hidden = nome !== perfil;
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      mostrarAba(aba.getAttribute("data-perfil"));
    });
  });

  function mostrarErros(formulario, erros) {
    var caixa = formulario.querySelector(".erros");
    caixa.textContent = "";
    erros.forEach(function (erro) {
      var linha = document.createElement("p");
      linha.textContent = erro;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function mostrarOficio(oficio) {
    document.getElementById("oficio").textContent = oficio;
    secaoConfirmacao.hidden = false;
    areaFormularios.hidden = true;
  }

  function enviar(formulario, perfil) {
    var dados = { perfil: perfil };
    Array.prototype.forEach.call(formulario.elements, function (campo) {
      if (campo.name) {
        dados[campo.name] = campo.value;
      }
    });
    fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    }).then(function (resposta) {
      return resposta.json();
    }).then(function (resultado) {
      if (resultado.erros && resultado.erros.length) {
        mostrarErros(formulario, resultado.erros);
      } else {
        mostrarOficio(resultado.oficio);
      }
    });
  }

  Object.keys(formularios).forEach(function (perfil) {
    formularios[perfil].addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(formularios[perfil], perfil);
    });
  });

  mostrarAba("alunos");
})();
