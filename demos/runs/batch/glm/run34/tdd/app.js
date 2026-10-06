/* Comportamento de tela da solicitação de auxílio financeiro.
   A validação é do backend; aqui só se formata campo e se mostra a resposta. */

function milhar(numero) {
  var texto = String(numero);
  var saida = "";
  while (texto.length > 3) {
    saida = "." + texto.slice(-3) + saida;
    texto = texto.slice(0, -3);
  }
  return texto + saida;
}

function formatarValor(texto) {
  var digitos = texto.replace(/\D/g, "");
  if (!digitos) {
    return "";
  }
  var centavos = parseInt(digitos, 10);
  var reais = Math.floor(centavos / 100);
  var resto = centavos % 100;
  return "R$ " + milhar(reais) + "," + String(resto).padStart(2, "0");
}

function formatarCPF(texto) {
  var digitos = texto.replace(/\D/g, "");
  if (digitos.length !== 11) {
    return texto;
  }
  return digitos.slice(0, 3) + "." + digitos.slice(3, 6) + "." + digitos.slice(6, 9) + "-" + digitos.slice(9, 11);
}

function formatarCEP(texto) {
  var digitos = texto.replace(/\D/g, "");
  if (digitos.length !== 8) {
    return texto;
  }
  return digitos.slice(0, 5) + "-" + digitos.slice(5, 8);
}

function formatarData(texto) {
  var digitos = texto.replace(/\D/g, "");
  if (digitos.length !== 8) {
    return texto;
  }
  return digitos.slice(0, 2) + "/" + digitos.slice(2, 4) + "/" + digitos.slice(4, 8);
}

var FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data_nascimento: formatarData
};

function ligarFormatacao(form) {
  Object.keys(FORMATADORES).forEach(function (nome) {
    var campo = form.querySelector('input[name="' + nome + '"]');
    if (!campo) {
      return;
    }
    campo.addEventListener("blur", function () {
      campo.value = FORMATADORES[nome](campo.value);
    });
  });
}

function trocarAba(aba) {
  document.querySelectorAll(".aba").forEach(function (botao) {
    botao.classList.toggle("ativa", botao === aba);
  });
  document.querySelectorAll(".conteudo").forEach(function (secao) {
    secao.classList.toggle("oculto", secao.id !== "conteudo-" + aba.dataset.aba);
  });
}

function mostrarErros(form, erros) {
  var caixa = document.getElementById("erros-" + form.dataset.aba);
  caixa.innerHTML = "";
  erros.forEach(function (mensagem) {
    var linha = document.createElement("p");
    linha.textContent = mensagem;
    caixa.appendChild(linha);
  });
}

function mostrarOficio(oficio) {
  document.getElementById("paginas").classList.add("oculto");
  document.getElementById("confirmacao").classList.remove("oculto");
  document.getElementById("oficio").textContent = oficio;
}

function enviar(form) {
  var moldura = document.getElementById("moldura");
  moldura.onload = function () {
    var resposta;
    try {
      resposta = JSON.parse(moldura.contentDocument.body.textContent);
    } catch (erro) {
      return;
    }
    if (resposta.ok) {
      mostrarOficio(resposta.oficio);
    } else {
      mostrarErros(form, resposta.erros);
    }
  };
  form.action = "/solicitacao";
  form.target = "moldura";
  form.submit();
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".aba").forEach(function (aba) {
    aba.addEventListener("click", function () {
      trocarAba(aba);
    });
  });
  document.querySelectorAll("form").forEach(function (form) {
    ligarFormatacao(form);
    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      enviar(form);
    });
  });
});
