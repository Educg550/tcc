(function () {
  "use strict";

  let abaAtual = "ALUNOS";

  const abas = document.querySelectorAll(".aba");
  const formularios = document.querySelectorAll(".formulario");

  abas.forEach(function (botao) {
    botao.addEventListener("click", function () {
      abaAtual = botao.dataset.aba;
      abas.forEach(function (b) { b.classList.toggle("ativa", b === botao); });
      formularios.forEach(function (f) {
        f.classList.toggle("ativo", f.dataset.aba === abaAtual);
      });
    });
  });

  function formatarValor(digitos) {
    digitos = digitos.replace(/\D/g, "");
    if (!digitos) return "";
    digitos = digitos.padStart(3, "0");
    const centavos = digitos.slice(-2);
    let reais = digitos.slice(0, -2).replace(/^0+(?=\d)/, "");
    reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + reais + "," + centavos;
  }

  function formatarCPF(digitos) {
    digitos = digitos.replace(/\D/g, "").slice(0, 11);
    if (digitos.length <= 3) return digitos;
    if (digitos.length <= 6) return digitos.slice(0, 3) + "." + digitos.slice(3);
    if (digitos.length <= 9) return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." + digitos.slice(6);
    return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." + digitos.slice(6, 9) + "-" + digitos.slice(9);
  }

  function formatarCEP(digitos) {
    digitos = digitos.replace(/\D/g, "").slice(0, 8);
    if (digitos.length <= 5) return digitos;
    return digitos.slice(0, 5) + "-" + digitos.slice(5);
  }

  function formatarData(digitos) {
    digitos = digitos.replace(/\D/g, "").slice(0, 8);
    if (digitos.length <= 2) return digitos;
    if (digitos.length <= 4) return digitos.slice(0, 2) + "/" + digitos.slice(2);
    return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4);
  }

  function ligarFormatacao(input, fn) {
    input.addEventListener("blur", function () {
      input.value = fn(input.value);
    });
  }

  formularios.forEach(function (form) {
    const valor = form.querySelector('input[name="valor"]');
    const cpf = form.querySelector('input[name="cpf"]');
    const cep = form.querySelector('input[name="cep"]');
    const dataNasc = form.querySelector('input[name="data_nascimento"]');
    ligarFormatacao(valor, formatarValor);
    ligarFormatacao(cpf, formatarCPF);
    ligarFormatacao(cep, formatarCEP);
    ligarFormatacao(dataNasc, formatarData);

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      const aba = form.dataset.aba;
      const dados = { aba: aba };
      form.querySelectorAll("input, select, textarea").forEach(function (campo) {
        dados[campo.name] = campo.value;
      });

      fetch("/api/solicitar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      })
        .then(function (resposta) { return resposta.json(); })
        .then(function (res) {
          const caixaErros = document.getElementById("erros-" + aba);
          if (!res.ok) {
            caixaErros.textContent = res.erros.join("\n");
            caixaErros.hidden = false;
            return;
          }
          caixaErros.hidden = true;
          document.getElementById("pagina-formulario").hidden = true;
          const confirmacao = document.getElementById("pagina-confirmacao");
          confirmacao.hidden = false;
          document.getElementById("oficio").textContent = res.oficio;
        });
    });
  });
})();
