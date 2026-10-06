const $ = (s, c) => (c || document).querySelector(s);
const $$ = (s, c) => Array.from((c || document).querySelectorAll(s));

const digit = (v) => v.replace(/\D/g, "");
const centavos = (d) => {
  const n = BigInt(d || "0");
  const c = Number(n % 100n);
  const i = (n / 100n).toString();
  return "R$ " + i.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + String(c).padStart(2, "0");
};
const cpf = (d) =>
  d.replace(/(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})/, (_, a, b, c, e) =>
    a + (b ? "." + b : "") + (c ? "." + c : "") + (e ? "-" + e : ""));
const cep = (d) => d.replace(/(\d{5})(\d{0,3})/, (_, a, b) => a + (b ? "-" + b : ""));
const data = (d) => d.replace(/(\d{2})(\d{0,2})(\d{0,4})/, (_, a, b, c) => a + (b ? "/" + b : "") + (c ? "/" + c : ""));

const FORMATOS = [
  [".fmt-valor", digit, centavos],
  [".fmt-cpf", digit, cpf],
  [".fmt-cep", digit, cep],
  [".fmt-data", digit, data],
];
$$("input").forEach((inp) => {
  for (const [sel, getD, fmt] of FORMATOS) {
    if (!inp.matches(sel)) continue;
    inp.addEventListener("blur", () => { inp.value = fmt(getD(inp.value)); });
  }
});

const abas = $$(".tab");
abas.forEach((btn) => {
  btn.addEventListener("click", () => {
    abas.forEach((b) => {
      const atv = b === btn;
      b.classList.toggle("active", atv);
      b.setAttribute("aria-selected", atv ? "true" : "false");
    });
    $("#painel-alunos").classList.toggle("active", btn.dataset.tab === "alunos");
    $("#painel-docentes").classList.toggle("active", btn.dataset.tab === "docentes");
  });
});

function dadosDoForm(form) {
  const dados = {};
  $$("input, select, textarea", form).forEach((el) => {
    if (el.name) dados[el.name] = el.value;
  });
  return dados;
}

function mostrarErros(panel, erros) {
  const box = $(".erros", panel);
  box.innerHTML = "";
  erros.forEach((e) => {
    const li = document.createElement("div");
    li.textContent = e;
    box.appendChild(li);
  });
  box.hidden = erros.length === 0;
}

const voltar = $("#voltar");
function irParaConfirmacao(txt) {
  $("#oficio").textContent = txt;
  $("#painel-alunos").classList.remove("active");
  $("#painel-docentes").classList.remove("active");
  $$(".tab").forEach((b) => b.classList.remove("active"));
  $("#app").hidden = true;
  $("#confirmacao").hidden = false;
  window.scrollTo(0, 0);
}

$$("form").forEach((form) => {
  $(".erros", form.parentElement).hidden = true;
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const aba = form.dataset.tab;
    const panel = $("#painel-" + aba);
    mostrarErros(panel, []);
    let resp;
    try {
      resp = await fetch("/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aba: aba, dados: dadosDoForm(form) }),
      });
    } catch (e) {
      mostrarErros(panel, ["Falha ao contatar o servidor"]);
      return;
    }
    if (!resp.ok) {
      mostrarErros(panel, ["Falha ao contatar o servidor"]);
      return;
    }
    const j = await resp.json();
    if (!j.ok) {
      mostrarErros(panel, j.erros);
      return;
    }
    panel.querySelector(".erros").hidden = true;
    irParaConfirmacao(j.oficio);
  });
});

voltar.addEventListener("click", () => {
  $("#confirmacao").hidden = true;
  $("#app").hidden = false;
  abas[0].click();
});
