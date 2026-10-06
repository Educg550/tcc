function soDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

function formatarValor(valor) {
  var digitos = soDigitos(valor);
  if (!digitos) {
    return "";
  }
  var centavos = digitos.slice(-2).padStart(2, "0");
  var reais = digitos.slice(0, -2) || "0";
  reais = reais.replace(/^0+(?=\d)/, "");
  reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + centavos;
}

function formatarCpf(valor) {
  var d = soDigitos(valor).slice(0, 11);
  if (d.length > 9) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }
  if (d.length > 6) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  }
  if (d.length > 3) {
    return d.slice(0, 3) + "." + d.slice(3);
  }
  return d;
}

function formatarCep(valor) {
  var d = soDigitos(valor).slice(0, 8);
  if (d.length > 5) {
    return d.slice(0, 5) + "-" + d.slice(5);
  }
  return d;
}

function formatarData(valor) {
  var d = soDigitos(valor).slice(0, 8);
  if (d.length > 4) {
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }
  if (d.length > 2) {
    return d.slice(0, 2) + "/" + d.slice(2);
  }
  return d;
}

var FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

function mostrarErros(form, mensagens) {
  var caixa = form.querySelector(".erros");
  caixa.innerHTML = "";
  mensagens.forEach(function (mensagem) {
    var linha = document.createElement("div");
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
  caixa.classList.remove("oculto");
}

function limparErros(form) {
  var caixa = form.querySelector(".erros");
  caixa.innerHTML = "";
  caixa.classList.add("oculto");
}

function mostrarConfirmacao(oficio) {
  document.getElementById("oficio").textContent = oficio;
  document.getElementById("tela-formulario").classList.add("oculto");
  document.getElementById("tela-confirmacao").classList.remove("oculto");
}

function enviar(form) {
  var dados = { aba: form.dataset.aba };
  form.querySelectorAll("input, select, textarea").forEach(function (campo) {
    if (campo.name) {
      dados[campo.name] = campo.value;
    }
  });

  fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  })
    .then(function (resposta) {
      return resposta.json();
    })
    .then(function (resultado) {
      if (!resultado.ok) {
        mostrarErros(form, resultado.erros);
        return;
      }
      limparErros(form);
      mostrarConfirmacao(resultado.oficio);
    });
}

document.addEventListener("DOMContentLoaded", function () {
  var abas = Array.prototype.slice.call(document.querySelectorAll(".aba"));
  var formularios = Array.prototype.slice.call(document.querySelectorAll(".formulario"));

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      formularios.forEach(function (form) {
        form.classList.toggle("oculto", form.dataset.aba !== aba.dataset.aba);
      });
    });
  });

  formularios.forEach(function (form) {
    form.querySelectorAll("[data-formatar]").forEach(function (campo) {
      campo.addEventListener("blur", function () {
        campo.value = FORMATADORES[campo.dataset.formatar](campo.value);
      });
    });

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form);
    });
  });
});
