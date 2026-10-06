function formataValor(texto) {
  const digitos = texto.replace(/\D/g, "");
  if (!digitos) return "";
  const n = parseInt(digitos, 10);
  const reais = Math.floor(n / 100).toLocaleString("pt-BR");
  const centavos = String(n % 100).padStart(2, "0");
  return `R$ ${reais},${centavos}`;
}

function formataCpf(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 11);
  let saida = d.slice(0, 3);
  if (d.length > 3) saida += "." + d.slice(3, 6);
  if (d.length > 6) saida += "." + d.slice(6, 9);
  if (d.length > 9) saida += "-" + d.slice(9, 11);
  return saida;
}

function formataCep(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 8);
  if (d.length > 5) return d.slice(0, 5) + "-" + d.slice(5);
  return d;
}

function formataData(texto) {
  const d = texto.replace(/\D/g, "").slice(0, 8);
  let saida = d.slice(0, 2);
  if (d.length > 2) saida += "/" + d.slice(2, 4);
  if (d.length > 4) saida += "/" + d.slice(4, 8);
  return saida;
}

function mostraAba(tipo) {
  const abaAlunos = document.getElementById("aba-alunos");
  const abaDocentes = document.getElementById("aba-docentes");
  const painelAlunos = document.getElementById("painel-alunos");
  const painelDocentes = document.getElementById("painel-docentes");
  const alunosAtivo = tipo === "alunos";
  abaAlunos.classList.toggle("ativa", alunosAtivo);
  abaAlunos.setAttribute("aria-selected", String(alunosAtivo));
  abaDocentes.classList.toggle("ativa", !alunosAtivo);
  abaDocentes.setAttribute("aria-selected", String(!alunosAtivo));
  painelAlunos.hidden = !alunosAtivo;
  painelDocentes.hidden = alunosAtivo;
}

document.getElementById("aba-alunos").addEventListener("click", () => mostraAba("alunos"));
document.getElementById("aba-docentes").addEventListener("click", () => mostraAba("docentes"));

function bindFormatacao(form) {
  const valor = form.querySelector('[name="valor"]');
  const cpf = form.querySelector('[name="cpf"]');
  const cep = form.querySelector('[name="cep"]');
  const nascimento = form.querySelector('[name="nascimento"]');
  valor.addEventListener("blur", () => { valor.value = formataValor(valor.value); });
  cpf.addEventListener("blur", () => { cpf.value = formataCpf(cpf.value); });
  cep.addEventListener("blur", () => { cep.value = formataCep(cep.value); });
  nascimento.addEventListener("blur", () => { nascimento.value = formataData(nascimento.value); });
}

bindFormatacao(document.getElementById("form-alunos"));
bindFormatacao(document.getElementById("form-docentes"));

function mostraErros(form, erros) {
  const div = form.parentElement.querySelector(".erros");
  div.innerHTML = "";
  erros.forEach(msg => {
    const p = document.createElement("p");
    p.textContent = msg;
    div.appendChild(p);
  });
  div.hidden = false;
}

function limpaErros(form) {
  const div = form.parentElement.querySelector(".erros");
  div.innerHTML = "";
  div.hidden = true;
}

async function envia(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const tipo = form.id === "form-alunos" ? "aluno" : "docente";
  const dados = Object.fromEntries(new FormData(form));
  dados.tipo = tipo;
  const resposta = await fetch("/api/solicitacao", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados)
  });
  const json = await resposta.json();
  if (json.ok) {
    document.querySelector("main").hidden = true;
    document.querySelector(".abas").hidden = true;
    document.getElementById("oficio").textContent = json.oficio;
    document.getElementById("confirmacao").hidden = false;
  } else {
    mostraErros(form, json.erros);
  }
}

document.getElementById("form-alunos").addEventListener("submit", envia);
document.getElementById("form-docentes").addEventListener("submit", envia);
