const BASE_URL = "";

async function getJSON(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => null);
  if (payload && payload.errors) {
    throw new Error(payload.errors[0]);
  }
  if (!response.ok) {
    throw new Error(payload && payload.detail ? payload.detail : "Request failed");
  }
  return payload;
}

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  if (attrs) {
    for (const [key, value] of Object.entries(attrs)) {
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value);
    }
  }
  for (const child of children) {
    if (child == null) continue;
    node.append(child.nodeType ? child : document.createTextNode(String(child)));
  }
  return node;
}

function renderHome() {
  const app = document.getElementById("app");
  app.replaceChildren();
  const actions = el("div", { class: "home-actions" },
    el("a", { class: "btn", href: "#", onclick: (event) => { event.preventDefault(); renderFiles(); } }, "Arquivos"),
    el("a", { class: "btn", href: "#", onclick: (event) => { event.preventDefault(); renderQuery(); } }, "Consulta"),
  );
  const intro = el("p", null, "API do projeto Quantum Codecs.");
  app.append(actions, intro);
}

function renderFiles() {
  const app = document.getElementById("app");
  app.replaceChildren();
  const heading = el("h2", null, "Arquivos do pacote");
  app.append(heading);
  getJSON("/files")
    .then((data) => {
      const items = data.entries.map((entry) =>
        el("li", null,
          el("code", { text: entry.path }),
          el("span", { text: `${entry.lines} linhas, ${entry.size} bytes` }),
        ),
      );
      const list = el("ul", { class: "file-list" }, ...items);
      app.append(list);
      const back = el("button", { class: "btn", onclick: renderHome }, "Voltar");
      app.append(back);
    })
    .catch((error) => {
      const box = el("div", { class: "errors", text: error.message });
      app.append(box);
    });
}

function renderQuery() {
  const app = document.getElementById("app");
  app.replaceChildren();
  const input = el("input", { type: "text", placeholder: "ex.: qc_core/packets.py" });
  const label = el("label", { text: "Arquivo" });
  const viewer = el("div", { id: "qviewer" },
    label,
    input,
    el("label", { text: "Conteúdo" }),
    el("div", null, ""),
    el("textarea", { readonly: "readonly" }),
  );
  const button = el("button", { class: "btn" }, "Ver arquivo");
  button.addEventListener("click", () => {
    const target = input.value.trim();
    if (!target) return;
    getJSON(`/files/${target}`)
      .then((text) => {
        const box = viewer.querySelector("textarea");
        box.value = text;
      })
      .catch((error) => {
        const box = viewer.querySelector("textarea");
        box.value = "Erro: " + error.message;
      });
  });
  app.append(viewer, button);
}

renderHome();
