const CAMPOS_ALUNOS = [
  "nome_completo", "n_usp", "programa", "nivel", "tipo_de_auxilio",
  "email", "nome_do_evento", "periodo_do_evento", "cidade_do_evento",
  "estado_do_evento", "pais_do_evento", "link_do_evento", "valor_solicitado",
  "detalhamento_do_pedido", "apresentacao_de_trabalho", "data_de_nascimento",
  "logradouro", "numero", "complemento", "bairro", "cep", "cidade",
  "estado", "cpf", "rg", "banco", "agencia", "conta",
];

const CAMPOS_DOCENTES = CAMPOS_ALUNOS.filter((c) => c !== "nivel" && c !== "tipo_de_auxilio");

function formatarMoeda(digitos) {
  const limpos = (digitos || "").replace(/\D/g, "");
  if (!limpos) return "";
  const centavos = parseInt(limpos, 10);
  const reais = Math.floor(centavos / 100).toLocaleString("pt-BR");
  const resto = String(centavos % 100).padStart(2, "0");
  return `R$ ${reais},${resto}`;
}

function formatarCpf(valor) {
  const d = (valor || "").replace(/\D/g, "").slice(0, 11);
  return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4")
          .replace(/(\d{3})(\d{3})$/, "$1.$2")
          .replace(/^(\d{3})(\d{3})(\d{3})$/, "$1.$2.$3");
}

function formatarCep(valor) {
  const d = (valor || "").replace(/\D/g, "").slice(0, 8);
  return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
}

function formatarData(valor) {
  const d = (valor || "").replace(/\D/g, "").slice(0, 8);
  if (d.length > 4) return `${d.slice(0, 2)}/${d.slice(2, 4)}/${d.slice(4)}`;
  if (d.length > 2) return `${d.slice(0, 2)}/${d.slice(2)}`;
  return d;
}

function montarLigacoes() {
  document.querySelectorAll("[data-mascara]").forEach((campo) => {
    campo.addEventListener("blur", () => {
      const tipo = campo.dataset.mascara;
      const d = campo.value.replace(/\D/g, "");
      if (tipo === "moeda") campo.value = d ? formatarMoeda(d) : "";
      if (tipo === "cpf") campo.value = formatarCpf(d);
      if (tipo === "cep") campo.value = formatarCep(d);
      if (tipo === "data") campo.value = formatarData(d);
    });
  });

  document.querySelectorAll(".aba").forEach((botao) => {
    botao.addEventListener("click", () => trocarAba(botao.dataset.aba));
  });

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (e) => enviarFormulario(e, form));
  });
}

function trocarAba(nome) {
  document.querySelectorAll(".aba").forEach((b) => b.classList.toggle("ativa", b.dataset.aba === nome));
  document.querySelectorAll(".painel").forEach((p) => {
    p.classList.toggle("ativo", p.id === `painel-${nome}`);
  });
}

async function enviarFormulario(evento, form) {
  evento.preventDefault();
  const aba = form.dataset.aba;
  const dados = Object.fromEntries(new FormData(form).entries());
  const errosUl = form.querySelector(".erros");
  errosUl.innerHTML = "";
  errosUl.style.display = "none";

  try {
    const resposta = await fetch("/enviar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ aba, ...dados }),
    });
    const corpo = await resposta.json();
    if (!corpo.ok) {
      corpo.erros.forEach((msg) => {
        const li = document.createElement("li");
        li.textContent = msg;
        errosUl.appendChild(li);
      });
      errosUl.style.display = "block";
      return;
    }
    document.getElementById("oficio").textContent = corpo.oficio;
    document.getElementById("paginas").hidden = true;
    document.getElementById("confirmacao").hidden = false;
  } catch (erro) {
    const li = document.createElement("li");
    li.textContent = "Falha de comunicação com o servidor. Tente novamente.";
    errosUl.appendChild(li);
    errosUl.style.display = "block";
  }
}

document.addEventListener("DOMContentLoaded", montarLigacoes);
