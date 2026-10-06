// Comportamento de tela: abas, formatação dos campos e envio das solicitações.

function alternarAba(nome) {
  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.classList.toggle("ativa", aba.dataset.aba === nome);
  });
  document.querySelectorAll(".painel").forEach(function (painel) {
    painel.classList.toggle("visivel", painel.id === "aba-" + nome);
  });
}

document.querySelectorAll(".aba").forEach(function (aba) {
  aba.addEventListener("click", function () {
    alternarAba(aba.dataset.aba);
  });
});

// Formatação dos campos: o usuário digita dígitos, o backend devolve o formato.
async function formatarCampo(entrada) {
  const resposta = await fetch("/api/formata", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      campo: entrada.dataset.formata,
      valor: entrada.value,
    }),
  });
  const dados = await resposta.json();
  entrada.value = dados.formatado;
}

document.querySelectorAll("[data-formata]").forEach(function (entrada) {
  entrada.addEventListener("blur", function () {
    formatarCampo(entrada);
  });
});

function montarErros(div, erros) {
  div.replaceChildren();
  erros.forEach(function (mensagem) {
    const linha = document.createElement("p");
    linha.textContent = mensagem;
    div.appendChild(linha);
  });
}

function configurarFormulario(form) {
  const aba = form.id.replace("form-", "");
  const divErros = document.getElementById("erros-" + aba);

  form.addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const dados = { tipo: aba };
    new FormData(form).forEach(function (valor, campo) {
      dados[campo] = valor;
    });
    const resposta = await fetch("/api/validar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();
    montarErros(divErros, resultado.erros);
    if (resultado.erros.length === 0) {
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("confirmacao").classList.remove("oculto");
      document.querySelectorAll(".painel").forEach(function (painel) {
        painel.classList.remove("visivel");
      });
      document.querySelector(".abas").classList.add("oculto");
    }
  });
}

document.querySelectorAll("form").forEach(configurarFormulario);

document.getElementById("voltar").addEventListener("click", function () {
  document.getElementById("confirmacao").classList.add("oculto");
  document.querySelector(".abas").classList.remove("oculto");
  alternarAba("alunos");
});
