(function () {
  "use strict";

  function digitos(texto) {
    return String(texto).replace(/\D/g, "");
  }

  function formatarValor(texto) {
    var d = digitos(texto);
    if (!d) {
      return "";
    }
    var centavos = parseInt(d, 10);
    var reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + String(centavos % 100).padStart(2, "0");
  }

  function formatarCpf(texto) {
    var d = digitos(texto).slice(0, 11);
    if (d.length <= 3) return d;
    if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
    if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }

  function formatarCep(texto) {
    var d = digitos(texto).slice(0, 8);
    if (d.length <= 5) return d;
    return d.slice(0, 5) + "-" + d.slice(5);
  }

  function formatarData(texto) {
    var d = digitos(texto).slice(0, 8);
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  var FORMATADORES = {
    valor: formatarValor,
    cpf: formatarCpf,
    cep: formatarCep,
    data: formatarData
  };

  document.querySelectorAll("input[data-formato]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = FORMATADORES[campo.dataset.formato](campo.value);
    });
  });

  var abaAlunos = document.getElementById("aba-alunos");
  var abaDocentes = document.getElementById("aba-docentes");
  var formAlunos = document.getElementById("form-alunos");
  var formDocentes = document.getElementById("form-docentes");
  var secaoFormulario = document.getElementById("formulario");
  var secaoConfirmacao = document.getElementById("confirmacao");

  function ativarAba(mostrarAlunos) {
    abaAlunos.classList.toggle("ativa", mostrarAlunos);
    abaDocentes.classList.toggle("ativa", !mostrarAlunos);
    formAlunos.hidden = !mostrarAlunos;
    formDocentes.hidden = mostrarAlunos;
  }

  abaAlunos.addEventListener("click", function () { ativarAba(true); });
  abaDocentes.addEventListener("click", function () { ativarAba(false); });

  function mostrarErros(form, mensagens) {
    var caixa = form.querySelector(".erros");
    caixa.replaceChildren();
    mensagens.forEach(function (mensagem) {
      var linha = document.createElement("div");
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.hidden = false;
  }

  async function enviar(evento) {
    evento.preventDefault();
    var form = evento.target;
    var dados = Object.fromEntries(new FormData(form));
    dados.aba = form.id === "form-alunos" ? "alunos" : "docentes";
    var resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    var retorno = await resposta.();
    if (retorno.erros && retorno.erros.length) {
      mostrarErros(form, retorno.erros);
      return;
    }
    document.getElementById("oficio").textContent = retorno.oficio;
    secaoFormulario.hidden = true;
    secaoConfirmacao.hidden = false;
  }

  formAlunos.addEventListener("submit", enviar);
  formDocentes.addEventListener("submit", enviar);
})();
