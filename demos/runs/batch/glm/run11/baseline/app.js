const formularios = {
  alunos: document.getElementById("form-alunos"),
  docentes: document.getElementById("form-docentes"),
};

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    formularios.alunos.hidden = aba.dataset.aba !== "alunos";
    formularios.docentes.hidden = aba.dataset.aba !== "docentes";
  });
});

const formatadores = {
  valor_solicitado(texto) {
    const digitos = texto.replace(/\D/g, "");
    if (!digitos) {
      return "";
    }
    const centavos = parseInt(digitos, 10);
    const reais = String(Math.floor(centavos / 100)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `R$ ${reais},${String(centavos % 100).padStart(2, "0")}`;
  },
  cpf(texto) {
    const digitos = texto.replace(/\D/g, "").slice(0, 11);
    return digitos.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  },
  cep(texto) {
    const digitos = texto.replace(/\D/g, "").slice(0, 8);
    return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos;
  },
  data_nascimento(texto) {
    const digitos = texto.replace(/\D/g, "").slice(0, 8);
    return [digitos.slice(0, 2), digitos.slice(2, 4), digitos.slice(4)]
      .filter((parte) => parte)
      .join("/");
  },
};

document.querySelectorAll("input, textarea").forEach((campo) => {
  const formatar = formatadores[campo.name];
  if (formatar) {
    campo.addEventListener("blur", () => {
      campo.value = formatar(campo.value);
    });
  }
});

Object.values(formularios).forEach((formulario) => {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const mensagens = formulario.querySelector(".erros");
    mensagens.innerHTML = "";
    mensagens.hidden = true;

    const dados = {};
    formulario.querySelectorAll("input, select, textarea").forEach((campo) => {
      dados[campo.name] = campo.value;
    });

    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    const resultado = await resposta.json();

    if (resultado.oficio) {
      document.getElementById("oficio").textContent = resultado.oficio;
      document.getElementById("solicitacao").hidden = true;
      document.getElementById("confirmacao").hidden = false;
      return;
    }

    resultado.erros.forEach((mensagem) => {
      const linha = document.createElement("p");
      linha.textContent = mensagem;
      mensagens.appendChild(linha);
    });
    mensagens.hidden = false;
  });
});
