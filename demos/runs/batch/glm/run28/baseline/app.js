// alternância de abas
const botoesAba = document.querySelectorAll(".aba");
const formAlunos = document.getElementById("form-alunos");
const formDocentes = document.getElementById("form-docentes");
const errosAlunos = document.getElementById("erros-alunos");
const errosDocentes = document.getElementById("erros-docentes");
const confirmacao = document.getElementById("confirmacao");
const oficio = document.getElementById("oficio");
const main = document.querySelector("main");

const formularios = { alunos: formAlunos, docentes: formDocentes };
const errosDivs = { alunos: errosAlunos, docentes: errosDocentes };

function trocarAba(alvo) {
  botoesAba.forEach(function (btn) {
    btn.classList.toggle("ativa", btn.dataset.aba === alvo);
  });
  Object.keys(formularios).forEach(function (aba) {
    formularios[aba].classList.toggle("escondido", aba !== alvo);
    errosDivs[aba].hidden = aba !== alvo;
  });
}

botoesAba.forEach(function (btn) {
  btn.addEventListener("click", function () {
    trocarAba(btn.dataset.aba);
  });
});

// formatação automática dos campos monetários, cpf, cep e data
function soDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

function formatarMoeda(digitos) {
  const cents = parseInt(digitos || "0", 10);
  const reais = Math.floor(cents / 100);
  const centavos = String(cents % 100).padStart(2, "0");
  const partes = String(reais).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + partes + "," + centavos;
}

function formatarCPF(d) {
  return d.slice(0, 3) + (d.length > 3 ? "." + d.slice(3, 6) : "") +
         (d.length > 6 ? "." + d.slice(6, 9) : "") +
         (d.length > 9 ? "-" + d.slice(9, 11) : "");
}

function formatarCEP(d) {
  return d.slice(0, 5) + (d.length > 5 ? "-" + d.slice(5, 8) : "");
}

function formatarData(d) {
  return d.slice(0, 2) + (d.length > 2 ? "/" + d.slice(2, 4) : "") +
         (d.length > 4 ? "/" + d.slice(4, 8) : "");
}

function vincularFormatacao(form) {
  const mapa = {
    valor: formatarMoeda,
    cpf: formatarCPF,
    cep: formatarCEP,
    data_nascimento: formatarData,
  };
  Object.keys(mapa).forEach(function (campo) {
    const el = form.elements[campo];
    if (!el) return;
    el.addEventListener("blur", function () {
      const fn = mapa[campo];
      const digitos = campo === "valor" ? soDigitos(el.value) : soDigitos(el.value);
      if (!digitos) return;
      el.value = fn(digitos);
    });
  });
}

vincularFormatacao(formAlunos);
vincularFormatacao(formDocentes);

// envio para o backend
function montarDados(form) {
  const dados = { aba: form.dataset.aba };
  Array.prototype.forEach.call(form.elements, function (el) {
    if (!el.name || el.type === "submit" || el.type === "button") return;
    dados[el.name] = el.type === "checkbox" ? el.checked : el.value;
  });
  return dados;
}

function mostrarErros(aba, erros) {
  const div = errosDivs[aba];
  div.innerHTML = "";
  erros.forEach(function (msg) {
    const p = document.createElement("p");
    p.textContent = msg;
    div.appendChild(p);
  });
  div.hidden = erros.length === 0;
}

function enviar(form, event) {
  event.preventDefault();
  mostrarErros(form.dataset.aba, []);
  const dados = montarDados(form);
  fetch("/validar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  })
    .then(function (res) { return res.json(); })
    .then(function (res) {
      if (!res.ok) {
        mostrarErros(form.dataset.aba, res.erros);
        return;
      }
      oficio.textContent = res.oficio;
      confirmacao.hidden = false;
      main.hidden = true;
    });
}

formAlunos.addEventListener("submit", function (e) { enviar(formAlunos, e); });
formDocentes.addEventListener("submit", function (e) { enviar(formDocentes, e); });
