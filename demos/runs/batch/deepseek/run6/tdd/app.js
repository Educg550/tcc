(function () {
  "use strict";

  function soDigitos(v) {
    return v.replace(/\D/g, "");
  }

  function formataValor(v) {
    var d = soDigitos(v);
    if (!d) return "";
    d = d.replace(/^0+/, "") || "0";
    d = d.padStart(3, "0");
    var centavos = d.slice(-2);
    var inteiro = d.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return "R$ " + inteiro + "," + centavos;
  }

  function formataCpf(v) {
    var d = soDigitos(v).slice(0, 11);
    var r = d;
    if (d.length > 9) r = d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, "$1.$2.$3-$4");
    else if (d.length > 6) r = d.replace(/(\d{3})(\d{3})(\d{0,3})/, "$1.$2.$3");
    else if (d.length > 3) r = d.replace(/(\d{3})(\d{0,3})/, "$1.$2");
    return r;
  }

  function formataCep(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 5) return d.replace(/(\d{5})(\d{0,3})/, "$1-$2");
    return d;
  }

  function formataData(v) {
    var d = soDigitos(v).slice(0, 8);
    if (d.length > 4) return d.replace(/(\d{2})(\d{2})(\d{0,4})/, "$1/$2/$3");
    if (d.length > 2) return d.replace(/(\d{2})(\d{0,2})/, "$1/$2");
    return d;
  }

  var formatadores = {
    valor: formataValor,
    cpf: formataCpf,
    cep: formataCep,
    data_nascimento: formataData
  };

  function abaDoForm(form) {
    return form.id === "form-docentes" ? "docentes" : "alunos";
  }

  function formatarCampos(form) {
    Object.keys(formatadores).forEach(function (nome) {
      var input = form.elements[nome];
      if (input) input.value = formatadores[nome](input.value);
    });
  }

  function mostrarConfirmacao(oficio) {
    document.querySelector(".abas").classList.add("oculto");
    document.getElementById("painel-alunos").classList.add("oculto");
    document.getElementById("painel-docentes").classList.add("oculto");
    document.getElementById("oficio").textContent = oficio;
    document.getElementById("confirmacao").classList.remove("oculto");
  }

  function enviar(form) {
    formatarCampos(form);

    var dados = { aba: abaDoForm(form) };
    new FormData(form).forEach(function (valor, chave) {
      dados[chave] = typeof valor === "string" ? valor.trim() : valor;
    });

    fetch("/api/solicitar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados)
    })
      .then(function (r) { return r.json(); })
      .then(function (resposta) {
        var caixaErros = form.querySelector(".erros");
        if (!resposta.ok) {
          caixaErros.textContent = (resposta.erros || []).join("\n");
          caixaErros.hidden = false;
          return;
        }
        caixaErros.hidden = true;
        mostrarConfirmacao(resposta.oficio);
      })
      .catch(function () {
        var caixaErros = form.querySelector(".erros");
        caixaErros.textContent = "Não foi possível enviar a solicitação.";
        caixaErros.hidden = false;
      });
  }

  document.querySelectorAll("form").forEach(function (form) {
    Object.keys(formatadores).forEach(function (nome) {
      var input = form.elements[nome];
      if (!input) return;
      input.addEventListener("blur", function () {
        input.value = formatadores[nome](input.value);
      });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      enviar(form);
    });
  });

  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.addEventListener("click", function () {
      var alvo = botao.dataset.aba;
      document.querySelectorAll(".aba").forEach(function (b) {
        b.classList.toggle("ativa", b === botao);
      });
      document.getElementById("painel-alunos").classList.toggle("oculto", alvo !== "alunos");
      document.getElementById("painel-docentes").classList.toggle("oculto", alvo !== "docentes");
    });
  });
})();
