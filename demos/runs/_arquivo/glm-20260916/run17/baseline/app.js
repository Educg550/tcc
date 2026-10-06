"use strict";

const FORMATADORES = {
  valor: formatarValor,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData,
};

function soDigitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarValor(texto) {
  const digitos = soDigitos(texto);
  if (!digitos) {
    return "";
  }
  const [inteira, centavos] = (parseInt(digitos, 10) / 100).toFixed(2).split(".");
  const milhar = inteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + milhar + "," + centavos;
}

function formatarCpf(texto) {
  const d = soDigitos(texto).slice(0, 11);
  if (d.length > 9) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
  }
  if (d.length > 6) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  }
  if (d.length > 3) {
    return d.slice(0, 3) + "." + d.slice(3);
  }
  return d;
}

function formatarCep(texto) {
  const d = soDigitos(texto).slice(0, 8);
  return d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(texto) {
  const d = soDigitos(texto).slice(0, 8);
  if (d.length > 4) {
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }
  if (d.length > 2) {
    return d.slice(0, 2) + "/" + d.slice(2);
  }
  return d;
}

document.querySelectorAll("[data-formato]").forEach((campo) => {
  const reformatar = () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  };
  campo.addEventListener("input", reformatar);
  campo.addEventListener("blur", reformatar);
});

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll(".formulario").forEach((form) => {
      form.hidden = form.id !== aba.dataset.form;
    });
  });
});

document.querySelectorAll(".formulario").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { PERFIL: form.dataset.perfil };
    form.querySelectorAll("input, select, textarea").forEach((campo) => {
      if (campo.name) {
        dados[campo.name] = campo.value.trim();
      }
    });
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.();
    const quadroErros = form.querySelector(".erros");
    if (resultado.erros && resultado.erros.length) {
      quadroErros.replaceChildren(
        ...resultado.erros.map((mensagem) => {
          const linha = document.createElement("p");
          linha.textContent = mensagem;
          return linha;
        })
      );
      quadroErros.hidden = false;
      window.scrollTo(0, 0);
    } else {
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("formulario").hidden = true;
      document.getElementById("confirmacao").hidden = false;
      window.scrollTo(0, 0);
    }
  });
});
