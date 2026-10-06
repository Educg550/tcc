// Comportamento de tela: abas, formatação de campos e envio ao backend.

const CAMPOS_FORMATAR = {
  valor_solicitado: (d) => "R$ " + formatarBrl(d),
  cpf: formatarCpf,
  cep: formatarCep,
  data_de_nascimento: formatarData,
};

function apenasDigitos(texto) {
  return (texto || "").replace(/\D/g, "");
}

function formatarBrl(digitos) {
  let n = parseInt(digitos || "0", 10);
  const centavos = n % 100;
  const reais = Math.floor(n / 100);
  return reais.toLocaleString("pt-BR") + "," + String(centavos).padStart(2, "0");
}

function formatarCpf(d) {
  if (d.length > 9) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9, 11);
  }
  if (d.length > 6) {
    return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9);
  }
  if (d.length > 3) {
    return d.slice(0, 3) + "." + d.slice(3, 6);
  }
  return d;
}

function formatarCep(d) {
  if (d.length > 5) {
    return d.slice(0, 5) + "-" + d.slice(5, 8);
  }
  return d;
}

function formatarData(d) {
  if (d.length > 4) {
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4, 8);
  }
  if (d.length > 2) {
    return d.slice(0, 2) + "/" + d.slice(2, 4);
  }
  return d;
}

for (const [nome, formatar] of Object.entries(CAMPOS_FORMATAR)) {
  document.querySelectorAll(`[name="${nome}"]`).forEach((campo) => {
    campo.addEventListener("blur", () => {
      const formatado = formatar(apenasDigitos(campo.value));
      if (formatado !== campo.value) {
        campo.value = formatado;
      }
    });
  });
}

// Abas: troca sem recarregar e sem perder o que foi digitado.
const botões = document.querySelectorAll(".aba");

botões.forEach((botão) => {
  botão.addEventListener("click", () => {
    botões.forEach((b) => b.classList.toggle("ativa", b === botão));
    document.querySelectorAll(".formulario").forEach((form) => {
      const ativo = form.dataset.aba === botão.dataset.aba;
      form.hidden = !ativo;
    });
  });
});

async function enviar(form) {
  const dados = Object.fromEntries(new FormData(form));
  dados["aba"] = form.dataset.aba;
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  return resposta.json();
}

function mostrarErros(form, erros) {
  const caixa = form.querySelector(".erros");
  caixa.innerHTML = "";
  for (const mensagem of erros) {
    const p = document.createElement("p");
    p.textContent = mensagem;
    caixa.appendChild(p);
  }
  caixa.hidden = false;
}

document.querySelectorAll(".formulario").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const resposta = await enviar(form);
    if (resposta["ok"]) {
      document.getElementById("pagina").hidden = true;
      document.getElementById("oficio").textContent = resposta["oficio"];
      document.getElementById("confirmacao").hidden = false;
    } else {
      mostrarErros(form, resposta["erros"]);
    }
  });
});
