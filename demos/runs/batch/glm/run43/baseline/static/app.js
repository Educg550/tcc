const onlyDigits = (s) => s.replace(/\D/g, "");

function formatMoney(s) {
  const d = onlyDigits(s);
  if (!d) return "";
  const n = parseInt(d, 10);
  const reais = Math.floor(n / 100);
  const cent = String(n % 100).padStart(2, "0");
  return "R$ " + reais.toLocaleString("pt-BR") + "," + cent;
}

function formatCPF(s) {
  const d = onlyDigits(s).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9, 11);
}

function formatCEP(s) {
  const d = onlyDigits(s).slice(0, 8);
  return d.length <= 5 ? d : d.slice(0, 5) + "-" + d.slice(5, 8);
}

function formatDate(s) {
  const d = onlyDigits(s).slice(0, 8);
  let out = d.slice(0, 2);
  if (d.length >= 3) out += "/" + d.slice(2, 4);
  if (d.length >= 5) out += "/" + d.slice(4, 8);
  return out;
}

function setupForm(formId) {
  const form = document.getElementById(formId);
  const errorsBox = form.querySelector(".errors");

  form.querySelector(".money").addEventListener("blur", (e) => {
    const v = formatMoney(e.target.value);
    e.target.value = v;
  });
  form.querySelector(".cpf").addEventListener("blur", (e) => {
    e.target.value = formatCPF(e.target.value);
  });
  form.querySelector(".cep").addEventListener("blur", (e) => {
    e.target.value = formatCEP(e.target.value);
  });
  form.querySelector(".date").addEventListener("blur", (e) => {
    e.target.value = formatDate(e.target.value);
  });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    errorsBox.classList.remove("show");
    errorsBox.innerHTML = "";

    const data = { tipo: formId.replace("form-", "") };
    new FormData(form).forEach((v, k) => (data[k] = v.toString().trim()));

    try {
      const resp = await fetch("/api/solicitacao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await resp.json();

      if (!result.ok) {
        errorsBox.innerHTML = result.erros.map((e) => `<div>${e}</div>`).join("");
        errorsBox.classList.add("show");
        return;
      }

      document.getElementById("form-page").hidden = true;
      const page = document.getElementById("result-page");
      document.getElementById("oficio").textContent = result.oficio;
      page.hidden = false;
      window.scrollTo(0, 0);
    } catch (err) {
      errorsBox.innerHTML = "<div>Erro de comunicação com o servidor</div>";
      errorsBox.classList.add("show");
    }
  });
}

setupForm("form-alunos");
setupForm("form-docentes");

function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === name)
  );
  document.querySelectorAll(".panel").forEach((p) => {
    p.classList.toggle("active", p.id === "tab-" + name);
  });
}

document.querySelectorAll(".tab").forEach((t) => {
  t.addEventListener("click", () => showTab(t.dataset.tab));
});

document.getElementById("voltar").addEventListener("click", () => {
  document.getElementById("result-page").hidden = true;
  document.getElementById("form-page").hidden = false;
});
