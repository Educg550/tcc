(function () {
  "use strict";

  function apenasDigitos(texto) {
    return texto.replace(/\D/g, "");
  }

  function formatarMoeda(campo) {
    const digitos = apenasDigitos(campo.value).slice(0, 12);
    if (!digitos) {
      campo.value = "";
      return;
    }
    const centavos = parseInt(digitos, 10);
    const inteiro = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    campo.value = "R$ " + inteiro + "," + String(centavos % 100).padStart(2, "0");
  }

  function formatarCpf(campo) {
    const d = apenasDigitos(campo.value).slice(0, 11);
    let formatado = d;
    if (d.length > 9) {
      formatado = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
    } else if (d.length > 6) {
      formatado = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    } else if (d.length > 3) {
      formatado = d.slice(0, 3) + "." + d.slice(3);
    }
    campo.value = formatado;
  }

  function formatarCep(campo) {
    const d = apenasDigitos(campo.value).slice(0, 8);
    campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
  }

  function formatarData(campo) {
    const d = apenasDigitos(campo.value).slice(0, 8);
    let formatado = d;
    if (d.length > 4) {
      formatado = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
    } else if (d.length > 2) {
      formatado = d.slice(0, 2) + "/" + d.slice(2);
    }
    campo.value = formatado;
  }

  [
    ["moeda", formatarMoeda],
    ["cpf", formatarCpf],
    ["cep", formatarCep],
    ["data", formatarData]
  ].forEach(function (par) {
    document.querySelectorAll("." + par[0]).forEach(function (campo) {
      campo.addEventListener("blur", function () {
        par[1](campo);
      });
    });
  });

  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.addEventListener("click", function () {
      document.querySelectorAll(".aba").forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      document.querySelectorAll(".painel-form").forEach(function (painel) {
        painel.classList.toggle("ativo", painel.id === aba.dataset.alvo);
      });
    });
  });

  function mostrarErros(formulario, erros) {
    const caixa = formulario.querySelector(".erros");
    caixa.textContent = "";
    erros.forEach(function (mensagem) {
      const linha = document.createElement("div");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
  }

  function enviar(formulario, aba) {
    const dados = { aba: aba };
    formulario.querySelectorAll("[name]").forEach(function (campo) {
      dados[campo.name] = campo.value.trim();
    });
    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    })
      .then(function (resposta) {
        return resposta.();
      })
      .then(function (resultado) {
        if (resultado.oficio) {
          document.getElementById("oficio").textContent = resultado.oficio;
          document.getElementById("formularios").hidden = true;
          document.getElementById("confirmacao").classList.add("ativo");
          window.scrollTo(0, 0);
        } else {
          mostrarErros(formulario, resultado.erros || []);
        }
      });
  }

  [
    ["form-alunos", "alunos"],
    ["form-docentes", "docentes"]
  ].forEach(function (par) {
    const formulario = document.getElementById(par[0]);
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(formulario, par[1]);
    });
  });
})();
