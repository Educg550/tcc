(function () {
  "use strict";

  function soDigitos(texto) {
    return (texto.match(/\d/g) || []).join("");
  }

  function formatarValor(texto) {
    var d = soDigitos(texto);
    if (!d) {
      return "";
    }
    var total = parseInt(d, 10);
    var reais = Math.floor(total / 100);
    var centavos = total % 100;
    var parte = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + parte + "," + (centavos < 10 ? "0" : "") + centavos;
  }

  function formatarCpf(texto) {
    var d = soDigitos(texto).slice(0, 11);
    var saida = d.slice(0, 3);
    if (d.length > 3) {
      saida += "." + d.slice(3, 6);
    }
    if (d.length > 6) {
      saida += "." + d.slice(6, 9);
    }
    if (d.length > 9) {
      saida += "-" + d.slice(9);
    }
    return saida;
  }

  function formatarCep(texto) {
    var d = soDigitos(texto).slice(0, 8);
    if (d.length > 5) {
      return d.slice(0, 5) + "-" + d.slice(5);
    }
    return d;
  }

  function formatarData(texto) {
    var d = soDigitos(texto).slice(0, 8);
    var saida = d.slice(0, 2);
    if (d.length > 2) {
      saida += "/" + d.slice(2, 4);
    }
    if (d.length > 4) {
      saida += "/" + d.slice(4);
    }
    return saida;
  }

  function aoSair(id, formatador) {
    var campo = document.getElementById(id);
    if (campo) {
      campo.addEventListener("blur", function () {
        campo.value = formatador(campo.value);
      });
    }
  }

  ["alunos", "docentes"].forEach(function (aba) {
    aoSair(aba + "-valor", formatarValor);
    aoSair(aba + "-cpf", formatarCpf);
    aoSair(aba + "-cep", formatarCep);
    aoSair(aba + "-data", formatarData);
  });

  function ativarAba(aba) {
    document.getElementById("form-alunos").hidden = aba === "alunos";
    document.getElementById("form-docentes").hidden = aba === "docentes";
    document.getElementById("aba-alunos").classList.toggle("ativa", aba === "alunos");
    document.getElementById("aba-docentes").classList.toggle("ativa", aba === "docentes");
  }

  document.getElementById("aba-alunos").addEventListener("click", function () {
    ativarAba("alunos");
  });
  document.getElementById("aba-docentes").addEventListener("click", function () {
    ativarAba("docentes");
  });

  function coletar(form) {
    var dados = {};
    var campos = form.querySelectorAll("input[name], select[name], textarea[name]");
    for (var i = 0; i < campos.length; i++) {
      dados[campos[i].name] = campos[i].value;
    }
    return dados;
  }

  function mostrarErros(aba, erros) {
    var caixa = document.getElementById("erros-" + aba);
    caixa.textContent = "";
    erros.forEach(function (mensagem) {
      var linha = document.createElement("p");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  function enviar(aba, form) {
    document.getElementById("erros-" + aba).hidden = true;
    fetch("/api/solicitacao/" + aba, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(coletar(form))
    })
      .then(function (resposta) {
        return resposta.json();
      })
      .then(function (corpo) {
        if (corpo.ok) {
          document.getElementById("oficio").textContent = corpo.oficio;
          document.getElementById("pagina-formulario").hidden = true;
          document.getElementById("confirmacao").hidden = false;
        } else {
          mostrarErros(aba, corpo.erros);
        }
      });
  }

  ["alunos", "docentes"].forEach(function (aba) {
    document.getElementById("form-" + aba).addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(aba, evento.target);
    });
  });
})();
