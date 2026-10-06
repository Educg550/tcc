const abas = document.querySelectorAll(".aba");
const formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};
const erros = {
  alunos: document.getElementById("erros-alunos"),
  docentes: document.getElementById("erros-docentes"),
};
const paginaFormulario = document.getElementById("pagina-formulario");
const paginaConfirmacao = document.getElementById("pagina-confirmacao");
const oficio = document.getElementById("oficio");

function mostrarAba(nome) {
  abas.forEach(function (aba) {
    aba.classList.toggle("ativa", aba.dataset.aba === nome);
  });
  Object.keys(formularios).forEach(function (chave) {
    formularios[chave].hidden = chave !== nome;
    formularios[chave].classList.toggle("ativo", chave === nome);
  });
}

abas.forEach(function (aba) {
  aba.addEventListener("click", function () {
    mostrarAba(aba.dataset.aba);
  });
});

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(texto) {
  const centavos = soDigitos(texto);
  if (!centavos) {
    return "";
  }
  const inteiro = Math.floor(Number(centavos) / 100).toString();
  const decimal = centavos.slice(-2).padStart(2, "0");
  const partes = [];
  for (let i = inteiro.length; i > 0; i -= 3) {
    partes.unshift(inteiro.slice(Math.max(0, i - 3), i));
  }
  return "R$ " + partes.join(".") + "," + decimal;
}

function formatarCPF(texto) {
  const d = soDigitos(texto).slice(0, 11);
  let r = d.slice(0, 3);
  if (d.length > 3) r += "." + d.slice(3, 6);
  if (d.length > 6) r += "." + d.slice(6, 9);
  if (d.length > 9) r += "-" + d.slice(9, 11);
  return r;
}

function formatarCEP(texto) {
  const d = soDigitos(texto).slice(0, 8);
  if (d.length <= 5) {
    return d;
  }
  return d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  let r = d.slice(0, 2);
  if (d.length > 2) r += "/" + d.slice(2, 4);
  if (d.length > 4) r += "/" + d.slice(4, 8);
  return r;
}

const mascaras = {
  valor: formatarValor,
  cpf: formatarCPF,
  cep: formatarCEP,
  data: formatarData,
};

document.querySelectorAll("[data-mascara]").forEach(function (campo) {
  campo.addEventListener("blur", function () {
    campo.value = mascaras[campo.dataset.mascara](campo.value);
  });
});

function mostrarErros(aba, lista) {
  erros[aba].innerHTML = "";
  lista.forEach(function (mensagem) {
    const item = document.createElement("li");
    item.textContent = mensagem;
    erros[aba].appendChild(item);
  });
}

function valores(aba) {
  const dados = {};
  new FormData(formularios[aba]).forEach(function (valor, chave) {
    dados[chave] = valor;
  });
  dados["aba"] = aba === "alunos" ? "aluno" : "docente";
  return dados;
}

Object.keys(formularios).forEach(function (aba) {
  formularios[aba].addEventListener("submit", function (evento) {
    evento.preventDefault();
    fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(valores(aba)),
    })
      .then(function (resposta) {
        return resposta.json();
      })
      .then(function (dados) {
        if (dados.ok) {
          oficio.textContent = dados.oficio;
          paginaFormulario.hidden = true;
          paginaConfirmacao.hidden = false;
        } else {
          mostrarErros(aba, dados.erros);
        }
      });
  });
});

document.getElementById("voltar").addEventListener("click", function () {
  paginaConfirmacao.hidden = true;
  paginaFormulario.hidden = false;
});
