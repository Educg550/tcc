document.addEventListener("DOMContentLoaded", function () {
  var abas = document.querySelectorAll(".aba");
  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.classList.toggle("ativo", painel.id === "painel-" + aba.dataset.aba);
      });
    });
  });

  document.querySelectorAll("[data-mask]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = aplicarMascara(campo.dataset.mask, campo.value);
    });
  });

  document.querySelectorAll("form.formulario").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form);
    });
  });
});

function somenteDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

function formatarValor(valor) {
  var digitos = somenteDigitos(valor).replace(/^0+/, "");
  if (digitos === "") {
    return "";
  }
  digitos = digitos.padStart(3, "0");
  var centavos = digitos.slice(-2);
  var reais = digitos.slice(0, -2).replace(/^0+/, "") || "0";
  reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + centavos;
}

function formatarCpf(valor) {
  var d = somenteDigitos(valor).slice(0, 11);
  var saida = d.slice(0, 3);
  if (d.length > 3) saida += "." + d.slice(3, 6);
  if (d.length > 6) saida += "." + d.slice(6, 9);
  if (d.length > 9) saida += "-" + d.slice(9, 11);
  return saida;
}

function formatarCep(valor) {
  var d = somenteDigitos(valor).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  var d = somenteDigitos(valor).slice(0, 8);
  var partes = [];
  if (d.length > 0) partes.push(d.slice(0, 2));
  if (d.length > 2) partes.push(d.slice(2, 4));
  if (d.length > 4) partes.push(d.slice(4, 8));
  return partes.join("/");
}

function aplicarMascara(tipo, valor) {
  if (tipo === "valor") return formatarValor(valor);
  if (tipo === "cpf") return formatarCpf(valor);
  if (tipo === "cep") return formatarCep(valor);
  if (tipo === "data") return formatarData(valor);
  return valor;
}

function enviar(form) {
  var dados = {};
  new FormData(form).forEach(function (valor, chave) {
    dados[chave] = valor;
  });

  var painel = form.closest(".painel");
  var areaErros = painel.querySelector(".erros");

  fetch("/solicitar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  })
    .then(function (resposta) {
      return resposta.text().then(function (html) {
        return { ok: resposta.ok, html: html };
      });
    })
    .then(function (resultado) {
      if (resultado.ok) {
        painel.innerHTML = resultado.html;
      } else {
        areaErros.innerHTML = resultado.html;
      }
    });
}
