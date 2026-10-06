// Abas: alternância sem recarregar a página.
function mostraAba(nome) {
  document.querySelectorAll(".aba").forEach(function (b) {
    b.classList.toggle("ativa", b.dataset.aba === nome);
  });
  document.querySelectorAll(".painel").forEach(function (p) {
    p.classList.toggle("visivel", p.id === "painel-" + nome);
  });
}

function paraJson(form) {
  var dados = {};
  new FormData(form).forEach(function (v, k) {
    dados[k] = v;
  });
  return JSON.stringify(dados);
}

// Envio sem recarregar: o backend decide se é válido.
function envia(event, aba) {
  event.preventDefault();
  var form = document.getElementById("form-" + aba);
  var caixa = document.getElementById("erros-" + aba);
  caixa.innerHTML = "";
  fetch("/enviar", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "aba=" + aba + "&data=" + encodeURIComponent(paraJson(form)),
  })
    .then(function (r) {
      return r.json();
    })
    .then(function (resp) {
      if (resp.ok) {
        mostraConfirmacao(resp.oficio);
      } else {
        (resp.erros || []).forEach(function (e) {
          var item = document.createElement("p");
          item.textContent = e;
          caixa.appendChild(item);
        });
      }
    });
  return false;
}

function mostraConfirmacao(oficio) {
  document.querySelectorAll(".painel").forEach(function (p) {
    p.classList.remove("visivel");
  });
  document.querySelector(".abas").classList.add("oculto");
  document.getElementById("oficio").textContent = oficio;
  document.getElementById("confirmacao").classList.remove("oculto");
}

function voltaFormulario() {
  document.getElementById("confirmacao").classList.add("oculto");
  document.querySelector(".abas").classList.remove("oculto");
  mostraAba("ALUNOS");
}

// Máscaras: reformatam no momento em que o usuário sai do campo.
document.addEventListener("DOMContentLoaded", function () {
  function aplicaMascara(campo, formatar) {
    campo.addEventListener("blur", function () {
      var digitos = campo.value.replace(/\D/g, "");
      if (digitos) {
        campo.value = formatar(digitos);
      }
    });
  }

  function moeda(digitos) {
    var centavos = parseInt(digitos, 10);
    return (
      "R$ " +
      (centavos / 100)
        .toLocaleString("pt-BR", { minimumFractionDigits: 2 })
    );
  }

  function cpf(digitos) {
    return digitos
      .padStart(11, "0")
      .replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
  }

  function cep(digitos) {
    return digitsFix(digitos, 8).replace(/^(\d{5})(\d{3})$/, "$1-$2");
  }

  function digitsFix(d, n) {
    return d.slice(0, n);
  }

  function data(digitos) {
    return digitsFix(digitos, 8).replace(/^(\d{2})(\d{2})(\d{4})$/, "$1/$2/$3");
  }

  document
    .querySelectorAll('input[name="valor"]')
    .forEach(function (c) {
      aplicaMascara(c, moeda);
    });
  document
    .querySelectorAll('input[name="cpf"]')
    .forEach(function (c) {
      aplicaMascara(c, cpf);
    });
  document
    .querySelectorAll('input[name="cep"]')
    .forEach(function (c) {
      aplicaMascara(c, cep);
    });
  document
    .querySelectorAll('input[name="data_nascimento"]')
    .forEach(function (c) {
      aplicaMascara(c, data);
    });
});
