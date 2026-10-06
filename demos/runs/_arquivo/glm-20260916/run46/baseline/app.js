"use strict";

const ROTULOS = {
  nome_completo: "NOME COMPLETO - SEM ABREVIAR",
  nusp: "N. USP",
  programa: "PROGRAMA",
  nivel: "NÍVEL",
  tipo_auxilio: "TIPO DE AUXÍLIO",
  email: "E-MAIL",
  evento: "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
  periodo: "PERÍODO DO EVENTO, EXAME OU DEFESA",
  cidade_evento: "CIDADE DO EVENTO, EXAME OU DEFESA",
  estado_evento: "ESTADO DO EVENTO, EXAME OU DEFESA",
  pais_evento: "PAÍS DO EVENTO, EXAME OU DEFESA",
  link_evento: "LINK DO EVENTO, EXAME OU DEFESA",
  valor: "VALOR SOLICITADO (R$)",
  detalhamento: "DETALHAMENTO DO PEDIDO",
  apresentacao: "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
  data_nascimento: "DATA DE NASCIMENTO",
  logradouro: "LOGRADOURO",
  numero: "NÚMERO",
  complemento: "COMPLEMENTO",
  bairro: "BAIRRO",
  cep: "CEP",
  cidade: "CIDADE",
  estado: "ESTADO",
  cpf: "CPF (SEPARADOS POR PONTOS E TRAÇO)",
  rg: "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
  banco: "NOME DO BANCO",
  agencia: "NÚMERO DA AGÊNCIA",
  conta: "NÚMERO DA CONTA"
};

function digitos(texto) {
  return texto.replace(/\D/g, "");
}

function formatarMoeda(texto) {
  const d = digitos(texto);
  if (!d) return "";
  const centavos = String(parseInt(d, 10));
  const reais = (centavos.slice(0, -2) || "0").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return "R$ " + reais + "," + centavos.slice(-2).padStart(2, "0");
}

function formatarCpf(texto) {
  const d = digitos(texto).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return d.slice(0, 3) + "." + d.slice(3);
  if (d.length <= 9) return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6);
  return d.slice(0, 3) + "." + d.slice(3, 6) + "." + d.slice(6, 9) + "-" + d.slice(9);
}

function formatarCep(texto) {
  const d = digitos(texto).slice(0, 8);
  return d.length <= 5 ? d : d.slice(0, 5) + "-" + d.slice(5);
}

function formatarData(texto) {
  const d = digitos(texto).slice(0, 8);
  if (d.length <= 2) return d;
  if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
  return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
}

const FORMATADORES = {
  moeda: formatarMoeda,
  cpf: formatarCpf,
  cep: formatarCep,
  data: formatarData
};

document.querySelectorAll("input[data-formato]").forEach((campo) => {
  campo.addEventListener("blur", () => {
    campo.value = FORMATADORES[campo.dataset.formato](campo.value);
  });
});

document.querySelectorAll(".aba").forEach((aba) => {
  aba.addEventListener("click", () => {
    document.querySelectorAll(".aba").forEach((outra) => {
      outra.classList.toggle("ativa", outra === aba);
    });
    document.querySelectorAll("form.formulario").forEach((form) => {
      form.hidden = form.id !== aba.dataset.alvo;
    });
  });
});

document.querySelectorAll("form.formulario").forEach((form) => {
  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const dados = { aba: form.dataset.aba };
    form.querySelectorAll("[name]").forEach((campo) => {
      dados[ROTULOS[campo.name]] = campo.value;
    });
    const resposta = await fetch("/api/solicitacao", {
      method: "POST",
      headers: { "Content-Type": "application/" },
      body: JSON.stringify(dados)
    });
    const resultado = await resposta.();
    const caixa = form.querySelector(".erros");
    if (resultado.erros && resultado.erros.length > 0) {
      caixa.replaceChildren(
        ...resultado.erros.map((mensagem) => {
          const linha = document.createElement("p");
          linha.textContent = mensagem;
          return linha;
        })
      );
      caixa.hidden = false;
    } else {
      mostrarConfirmacao(resultado.oficio);
    }
  });
});

function mostrarConfirmacao(oficio) {
  document.querySelector(".abas").hidden = true;
  document.querySelectorAll("form.formulario").forEach((form) => {
    form.hidden = true;
  });
  const secao = document.createElement("section");
  secao.id = "confirmacao";
  const titulo = document.createElement("h2");
  titulo.textContent = "Solicitação registrada";
  const corpo = document.createElement("pre");
  corpo.className = "oficio";
  corpo.textContent = oficio;
  secao.append(titulo, corpo);
  document.getElementById("conteudo").replaceChildren(secao);
}
