const MASCARAS = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

function apenasDigitos(valor, limite) {
  return valor.replace(/\D/g, "").slice(0, limite);
}

function formatarValor(valor) {
  const digitos = apenasDigitos(valor, 15);
  if (!digitos) return "";
  const reais = (parseInt(digitos, 10) / 100).toFixed(2);
  const partes = reais.split(".");
  const inteiro = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + inteiro + "," + partes[1];
}

function formatarCPF(valor) {
  const d = apenasDigitos(valor, 11);
  let saida = d;
  if (d.length > 3) saida = d.slice(0, 3) + "." + d.slice(3);
  if (d.length > 6) saida = saida.slice(0, 7) + "." + d.slice(6);
  if (d.length > 9) saida = saida.slice(0, 11) + "-" + d.slice(9);
  return saida;
}

function formatarCEP(valor) {
  const d = apenasDigitos(valor, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(valor) {
  const d = apenasDigitos(valor, 8);
  let saida = d;
  if (d.length > 2) saida = d.slice(0, 2) + "/" + d.slice(2);
  if (d.length > 4) saida = saida.slice(0, 5) + "/" + d.slice(4);
  return saida;
}

function montarOficio(dados) {
  const alunos = dados.aba !== "docentes";
  const linhas = [
    "Interessada(o): " + dados.nome + " - " + dados.n_usp,
    "E-mail: " + dados.email,
    "Assunto: Solicitação de Auxílio Financeiro - " +
      (alunos ? dados.tipo_auxilio : "Verba do programa"),
    alunos
      ? "Programa: " + dados.programa + " - " + dados.nivel
      : "Programa: " + dados.programa,
    "",
    "A CCP-" + dados.programa +
      " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
    "interessada(o) acima, conforme segue:",
    "",
    "Dados do evento",
    "Evento: " + dados.evento,
    "Período: " + dados.periodo,
    "Local: " + dados.cidade_evento + " - " + dados.estado_evento + " - " + dados.pais,
  ];
  if (dados.link) {
    linhas.push("Link do evento: " + dados.link);
  }
  linhas.push("Apresentação de trabalho: " + dados.apresentacao);
  linhas.push("Valor solicitado: " + dados.valor);
  linhas.push("Detalhamento: " + dados.detalhamento);
  linhas.push("");
  linhas.push("Endereço da(o) interessada(o)");
  linhas.push(dados.logradouro + ", " + dados.numero);
  if (dados.complemento) {
    linhas.push("Complemento: " + dados.complemento);
  }
  linhas.push("CEP: " + dados.cep);
  linhas.push(dados.bairro + ", " + dados.cidade + " - " + dados.estado);
  linhas.push("");
  linhas.push("Dados para pagamento");
  linhas.push("Data de nascimento: " + dados.data_nascimento);
  linhas.push("CPF: " + dados.cpf);
  linhas.push("RG / RNM: " + dados.rg);
  linhas.push("Banco: " + dados.banco);
  linhas.push("Agência: " + dados.agencia);
  linhas.push("Conta: " + dados.conta);
  linhas.push("");
  linhas.push("Encaminhe-se ao Serviço Financeiro para providências.");
  return linhas.join("\n");
}

async function enviar(form) {
  const dados = Object.fromEntries(new FormData(form));
  const resposta = await fetch("/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const resultado = await resposta.json();
  const areaErros = form.querySelector(".erros");

  if (resultado.erros.length) {
    areaErros.innerHTML = "";
    resultado.erros.forEach(function (mensagem) {
      const linha = document.createElement("p");
      linha.textContent = mensagem;
      areaErros.appendChild(linha);
    });
    areaErros.hidden = false;
    return;
  }

  areaErros.hidden = true;
  document.getElementById("oficio").textContent = montarOficio(dados);
  document.querySelectorAll(".formulario").forEach(function (formulario) {
    formulario.hidden = true;
  });
  document.querySelector(".abas").hidden = true;
  document.getElementById("confirmacao").hidden = false;
}

document.addEventListener("DOMContentLoaded", function () {
  const abas = Array.from(document.querySelectorAll(".aba"));
  const formularios = Array.from(document.querySelectorAll(".formulario"));

  abas.forEach(function (aba) {
    aba.addEventListener("click", function () {
      abas.forEach(function (outra) {
        outra.classList.toggle("ativa", outra === aba);
      });
      formularios.forEach(function (formulario) {
        formulario.hidden = formulario.dataset.aba !== aba.dataset.aba;
      });
    });
  });

  document.querySelectorAll("[data-mascara]").forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = MASCARAS[campo.dataset.mascara](campo.value);
    });
  });

  formularios.forEach(function (formulario) {
    formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(formulario);
    });
  });
});
