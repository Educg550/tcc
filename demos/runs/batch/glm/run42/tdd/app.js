/* Comportamento de tela: alternância de abas e campos que se formatam sozinhos. */

function alternar(aba) {
  ["alunos", "docentes"].forEach(function (nome) {
    var ativo = nome === aba;
    var botao = document.getElementById("tab-" + nome);
    var formulario = document.getElementById("form-" + nome);
    botao.classList.toggle("ativa", ativo);
    botao.classList.toggle("inativa", !ativo);
    botao.setAttribute("aria-selected", String(ativo));
    formulario.classList.toggle("visivel", ativo);
    formulario.classList.toggle("oculto", !ativo);
  });
}

document.getElementById("tab-alunos").addEventListener("click", function () {
  alternar("alunos");
});
document.getElementById("tab-docentes").addEventListener("click", function () {
  alternar("docentes");
});

var formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes")
};
if (formularios.alunos.classList.contains("visivel")) {
  alternar("alunos");
} else if (formularios.docentes.classList.contains("visivel")) {
  alternar("docentes");
}

/* Máscaras: o usuário digita apenas dígitos, a pontuação é da aplicação. */

function separarMilhar(numero) {
  var texto = String(numero);
  var saida = "";
  while (texto.length > 3) {
    saida = "." + texto.slice(-3) + saida;
    texto = texto.slice(0, texto.length - 3);
  }
  return texto + saida;
}

function formatarMoeda(digitos) {
  if (!digitos) {
    return "";
  }
  var centavos = parseInt(digitos.slice(0, 15), 10);
  var centesimos = centavos % 100;
  return "R$ " + separarMilhar(Math.floor(centavos / 100)) + "," + (centesimos < 10 ? "0" : "") + centesimos;
}

function formatarCpf(digitos) {
  digitos = digitos.slice(0, 11);
  var saida = "";
  for (var i = 0; i < digitos.length; i++) {
    if (i === 3 || i === 6) {
      saida += ".";
    }
    if (i === 9) {
      saida += "-";
    }
    saida += digitos[i];
  }
  return saida;
}

function formatarCep(digitos) {
  digitos = digitos.slice(0, 8);
  return digitos.length > 5 ? digitos.slice(0, 5) + "-" + digitos.slice(5) : digitos;
}

function formatarData(digitos) {
  digitos = digitos.slice(0, 8);
  var saida = "";
  for (var i = 0; i < digitos.length; i++) {
    if (i === 2 || i === 4) {
      saida += "/";
    }
    saida += digitos[i];
  }
  return saida;
}

var mascaras = {
  valor: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data_nascimento: formatarData
};

Object.keys(mascaras).forEach(function (nome) {
  document.querySelectorAll('[name="' + nome + '"]').forEach(function (campo) {
    campo.addEventListener("blur", function () {
      campo.value = mascaras[nome](campo.value.replace(/\D/g, ""));
    });
  });
});
