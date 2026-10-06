function formatarMoeda(valor) {
  const digitos = valor.replace(/\D/g, "");
  if (!digitos) {
    return "";
  }
  const numero = parseInt(digitos, 10) / 100;
  return "R$ " + numero.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatarCPF(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 11);
  return digitos
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d)/, "$1.$2")
    .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatarCEP(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 8);
  return digitos.replace(/(\d{5})(\d)/, "$1-$2");
}

function formatarData(valor) {
  const digitos = valor.replace(/\D/g, "").slice(0, 8);
  return digitos.replace(/(\d{2})(\d)/, "$1/$2").replace(/(\d{2})(\d)/, "$1/$2");
}

function formatarCampo(campo) {
  const tipo = campo.dataset.formato;
  if (tipo === "moeda") {
    campo.value = formatarMoeda(campo.value);
  } else if (tipo === "cpf") {
    campo.value = formatarCPF(campo.value);
  } else if (tipo === "cep") {
    campo.value = formatarCEP(campo.value);
  } else if (tipo === "data") {
    campo.value = formatarData(campo.value);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const abas = document.querySelectorAll(".aba");
  const paineis = document.querySelectorAll(".painel");

  function trocarAba(nome) {
    abas.forEach(function (aba) {
      aba.classList.toggle("ativa", aba.dataset.aba === nome);
    });
    paineis.forEach(function (painel) {
      painel.classList.toggle("escondido", painel.dataset.aba !== nome);
    });
  }

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      trocarAba(aba.dataset.aba);
    });
  });

  document.querySelectorAll("[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      formatarCampo(campo);
    });
  });

  document.querySelectorAll(".formulario").forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      formulario.querySelectorAll("[data-formato]").forEach(formatarCampo);

      const dados = {};
      formulario.querySelectorAll("[name]").forEach(function (campo) {
        dados[campo.name] = campo.value;
      });

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aba: formulario.dataset.aba, dados: dados }),
      })
        .then(function (resposta) {
          return resposta.json();
        })
        .then(function (resultado) {
          const caixa = formulario.querySelector(".erros");
          if (resultado.ok) {
            caixa.classList.add("escondido");
            document.querySelector(".abas").classList.add("escondido");
            paineis.forEach(function (painel) {
              painel.classList.add("escondido");
            });
            document.querySelector("#oficio").textContent = resultado.oficio;
            document.querySelector("#confirmacao").classList.remove("escondido");
          } else {
            caixa.innerHTML = "";
            resultado.erros.forEach(function (mensagem) {
              const linha = document.createElement("p");
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            caixa.classList.remove("escondido");
          }
        });
    });
  });
});
