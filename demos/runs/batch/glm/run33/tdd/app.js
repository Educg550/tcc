function formatarMoeda(campo) {
  const digitos = campo.value.replace(/\D/g, "");
  if (!digitos) { campo.value = ""; return; }
  const inteiro = digits => {
    let texto = String(Math.floor(digits / 100));
    let grupos = [];
    while (texto.length > 3) {
      grupos.unshift(texto.slice(-3));
      texto = texto.slice(0, -3);
    }
    grupos.unshift(texto);
    return grupos.join(".");
  };
  campo.value = "R$ " + inteiro(Number(digitos)) + "," + digitos.slice(-2).padStart(2, "0");
}

function formatarCPF(campo) {
  let d = campo.value.replace(/\D/g, "").slice(0, 11);
  campo.value = d.length > 9
    ? d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9)
    : d;
}

function formatarCEP(campo) {
  let d = campo.value.replace(/\D/g, "").slice(0, 8);
  campo.value = d.length > 5 ? d.slice(0, 5) + "-" + d.slice(5) : d;
}

function formatarData(campo) {
  let d = campo.value.replace(/\D/g, "").slice(0, 8);
  campo.value = d.length > 4
    ? d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4)
    : d.length > 2 ? d.slice(0, 2) + "/" + d.slice(2) : d;
}

document.addEventListener("blur", e => {
  if (e.target.matches("[data-moeda]")) formatarMoeda(e.target);
  if (e.target.matches("[data-cpf]")) formatarCPF(e.target);
  if (e.target.matches("[data-cep]")) formatarCEP(e.target);
  if (e.target.matches("[data-data]")) formatarData(e.target);
}, true);

document.querySelectorAll(".aba").forEach(botao => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach(b => b.classList.remove("ativa"));
    botao.classList.add("ativa");
    const aba = botao.dataset.aba;
    document.getElementById("form-alunos").classList.toggle("visivel", aba === "alunos");
    document.getElementById("form-docentes").classList.toggle("visivel", aba === "docentes");
  });
});

function enviar(form) {
  form.addEventListener("submit", async ev => {
    ev.preventDefault();
    const aba = form.id === "form-alunos" ? "alunos" : "docentes";
    const dados = Object.fromEntries(new FormData(form).entries());
    dados.aba = aba;
    if (aba === "docentes") {
      dados.nivel = "";
      dados.tipo_auxilio = "";
    }
    const resposta = await fetch("/api/validar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dados),
    });
    if (!resposta.ok) return;
    const corpo = await resposta.json();
    const erros = document.getElementById("erros-" + aba);
    erros.innerHTML = "";
    if (corpo.ok) {
      document.getElementById("principal").hidden = true;
      document.querySelector("nav").hidden = true;
      document.getElementById("oficio").textContent = corpo.oficio;
      document.getElementById("confirmacao").hidden = false;
    } else {
      corpo.erros.forEach(msg => {
        const li = document.createElement("li");
        li.textContent = msg;
        erros.appendChild(li);
      });
      erros.hidden = corpo.erros.length === 0;
    }
  });
}

document.querySelectorAll("form").forEach(enviar);
