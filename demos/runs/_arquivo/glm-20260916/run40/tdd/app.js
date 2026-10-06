(function () {
  "use strict";

  const ABAS = ["alunos", "docentes"];

  function digitos(valor) {
    return String(valor).replace(/\D/g, "");
  }

  function formatarMoeda(valor) {
    const d = digitos(valor).replace(/^0+(?=\d)/, "");
    if (!d) {
      return "";
    }
    const centavos = parseInt(d, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
  }

  function formatarCpf(valor) {
    const d = digitos(valor).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function formatarCep(valor) {
    const d = digitos(valor).slice(0, 8);
    return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(valor) {
    const d = digitos(valor).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  [
    ["data-fmt-moeda", formatarMoeda],
    ["data-fmt-cpf", formatarCpf],
    ["data-fmt-cep", formatarCep],
    ["data-fmt-data", formatarData]
  ].forEach(function (par) {
    document.querySelectorAll("[" + par[0] + "]").forEach(function (campo) {
      campo.addEventListener("blur", function () {
        campo.value = par[1](campo.value);
      });
    });
  });

  function abrirAba(nome) {
    ABAS.forEach(function (aba) {
      document.getElementById("aba-" + aba).classList.toggle("ativa", aba === nome);
      document.getElementById("form-" + aba).hidden = aba !== nome;
    });
  }

  document.getElementById("aba-alunos").addEventListener("click", function () {
    abrirAba("alunos");
  });
  document.getElementById("aba-docentes").addEventListener("click", function () {
    abrirAba("docentes");
  });

  ABAS.forEach(function (aba) {
    const formulario = document.getElementById("form-" + aba);
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      const dados = {};
      Array.from(formulario.elements).forEach(function (campo) {
        if (campo.name) {
          dados[campo.name] = campo.value;
        }
      });
      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/" },
        body: JSON.stringify(dados)
      })
        .then(function (resposta) {
          return resposta.();
        })
        .then(function (corpo) {
          if (corpo.oficio) {
            document.getElementById("erros-" + aba).hidden = true;
            document.getElementById("solicitacao").hidden = true;
            document.getElementById("oficio").textContent = corpo.oficio;
            document.getElementById("confirmacao").hidden = false;
          } else {
            const caixa = document.getElementById("erros-" + aba);
            caixa.textContent = "";
            (corpo.erros || []).forEach(function (mensagem) {
              const linha = document.createElement("p");
              linha.textContent = mensagem;
              caixa.appendChild(linha);
            });
            caixa.hidden = false;
          }
        });
    });
  });
})();
