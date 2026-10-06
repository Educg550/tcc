function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(campo) {
  const d = digitos(campo.value).slice(0, 11);
  campo.value = d
    ? "R$ " + (Number(d) / 100).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : "";
}

function formatarCpf(campo) {
  const d = digitos(campo.value).slice(0, 11);
  if (d.length > 9) {
    campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  } else if (d.length > 6) {
    campo.value = d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  } else if (d.length > 3) {
    campo.value = d.slice(0, 3) + "." + d.slice(3);
  } else {
    campo.value = d;
  }
}

function formatarCep(campo) {
  const d = digitos(campo.value).slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(campo) {
  const d = digitos(campo.value).slice(0, 8);
  if (d.length > 4) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  } else if (d.length > 2) {
    campo.value = d.slice(0, 2) + "/" + d.slice(2);
  } else {
    campo.value = d;
  }
}

const formatadores = {
  "VALOR SOLICITADO (R$)": formatarValor,
  "CPF (SEPARADOS POR PONTOS E TRAÇO)": formatarCpf,
  "CEP": formatarCep,
  "DATA DE NASCIMENTO": formatarData,
};

document.querySelectorAll("form [name]").forEach(function (campo) {
  if (formatadores[campo.name]) {
    campo.addEventListener("blur", function () {
      formatadores[campo.name](campo);
    });
  }
});

const formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

const botoes = {
  alunos: document.getElementById("aba-alunos"),
  docentes: document.getElementById("aba-docentes"),
};

function abrirAba(nome) {
  Object.keys(formularios).forEach(function (chave) {
    formularios[chave].hidden = chave !== nome;
    botoes[chave].classList.toggle("ativa", chave === nome);
  });
}

botoes.alunos.addEventListener("click", function () { abrirAba("alunos"); });
botoes.docentes.addEventListener("click", function () { abrirAba("docentes"); });

Object.keys(formularios).forEach(function (aba) {
  formularios[aba].addEventListener("submit", async function (evento) {
    evento.preventDefault();
    const dados = {};
    formularios[aba].querySelectorAll("[name]").forEach(function (campo) {
      dados[campo.name] = campo.value;
    });
    const resposta = await fetch("/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify({ aba: aba, dados: dados }),
    });
    const conteudo = await resposta.();
    const localErros = document.getElementById("erros-" + aba);
    if (conteudo.erros.length > 0) {
      localErros.replaceChildren.apply(
        localErros,
        conteudo.erros.map(function (mensagem) {
          const linha = document.createElement("div");
          linha.textContent = mensagem;
          return linha;
        })
      );
      return;
    }
    localErros.replaceChildren();
    document.getElementById("formulario").hidden = true;
    document.getElementById("oficio").textContent = conteudo.oficio;
    document.getElementById("confirmacao").hidden = false;
  });
});
