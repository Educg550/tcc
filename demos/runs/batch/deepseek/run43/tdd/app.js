(function () {
  var abas = document.querySelectorAll(".aba");
  var areaFormulario = document.getElementById("area-formulario");
  var confirmacao = document.getElementById("confirmacao");

  function ativarAba(alvo) {
    abas.forEach(function (aba) {
      aba.classList.toggle("ativa", aba.dataset.aba === alvo);
    });
    document.querySelectorAll(".formulario").forEach(function (form) {
      form.classList.toggle("ativo", form.dataset.aba.toLowerCase() === alvo);
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      ativarAba(aba.dataset.aba);
    });
  });

  function soDigitos(valor) {
    return valor.replace(/\D/g, "");
  }

  function formatarValor(valor) {
    var digitos = soDigitos(valor);
    if (!digitos) return "";
    var centavos = parseInt(digitos, 10);
    var reais = Math.floor(centavos / 100);
    var resto = String(centavos % 100).padStart(2, "0");
    return "R$ " + reais.toLocaleString("pt-BR") + "," + resto;
  }

  function formatarCPF(valor) {
    var digitos = soDigitos(valor).slice(0, 11);
    var saida = digitos.slice(0, 3);
    if (digitos.length > 3) saida += "." + digitos.slice(3, 6);
    if (digitos.length > 6) saida += "." + digitos.slice(6, 9);
    if (digitos.length > 9) saida += "-" + digitos.slice(9, 11);
    return saida;
  }

  function formatarCEP(valor) {
    var digitos = soDigitos(valor).slice(0, 8);
    if (digitos.length > 5) return digitos.slice(0, 5) + "-" + digitos.slice(5);
    return digitos;
  }

  function formatarData(valor) {
    var digitos = soDigitos(valor).slice(0, 8);
    var saida = digitos.slice(0, 2);
    if (digitos.length > 2) saida += "/" + digitos.slice(2, 4);
    if (digitos.length > 4) saida += "/" + digitos.slice(4, 8);
    return saida;
  }

  var formatadores = {
    "VALOR SOLICITADO (R$)": formatarValor,
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": formatarCPF,
    "CEP": formatarCEP,
    "DATA DE NASCIMENTO": formatarData,
  };

  document.querySelectorAll(".formulario input[name]").forEach(function (campo) {
    var formatar = formatadores[campo.name];
    if (formatar) {
      campo.addEventListener("blur", function () {
        campo.value = formatar(campo.value);
      });
    }
  });

  function mostrarErros(form, mensagens) {
    var caixa = form.querySelector(".erros");
    caixa.textContent = "";
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("div");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.classList.add("ativo");
  }

  function mostrarConfirmacao(oficio) {
    areaFormulario.hidden = true;
    confirmacao.textContent = "";
    var titulo = document.createElement("h2");
    titulo.textContent = "Solicitação registrada";
    var texto = document.createElement("pre");
    texto.className = "oficio";
    texto.textContent = oficio;
    confirmacao.appendChild(titulo);
    confirmacao.appendChild(texto);
    confirmacao.hidden = false;
  }

  document.querySelectorAll(".formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      var dados = { aba: form.dataset.aba };
      form.querySelectorAll("[name]").forEach(function (campo) {
        dados[campo.name] = campo.value;
      });
      fetch("/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          if (!resultado.ok) {
            mostrarErros(form, resultado.erros);
            return;
          }
          form.querySelector(".erros").classList.remove("ativo");
          mostrarConfirmacao(resultado.oficio);
        });
    });
  });
})();
