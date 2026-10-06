(function () {
  'use strict';

  var CAMPOS_SOLICITANTE_BASE = [
    { chave: 'nome',       rotulo: 'NOME COMPLETO - SEM ABREVIAR', tipo: 'texto',        placeholder: 'Maria Aparecida da Silva', col: 4 },
    { chave: 'nusp',       rotulo: 'N. USP',                        tipo: 'texto',        placeholder: '12345678', col: 2 },
    { chave: 'programa',   rotulo: 'PROGRAMA',                      tipo: 'texto',        placeholder: 'Estatística', col: 3 },
    { chave: 'email',      rotulo: 'E-MAIL',                        tipo: 'texto',        placeholder: 'maria@ime.usp.br', col: 3 }
  ];

  var CAMPOS_SOLICITANTE_ALUNOS = [
    { chave: 'nivel',      rotulo: 'NÍVEL', tipo: 'select', opcoes: ['Mestrado', 'Doutorado'], col: 2 },
    { chave: 'tipo_auxilio', rotulo: 'TIPO DE AUXÍLIO', tipo: 'select', opcoes: ['Participação em evento', 'Banca de exame ou defesa', 'Outro'], col: 3 }
  ];

  var CAMPOS_EVENTO = [
    { chave: 'nome_evento', rotulo: 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA', tipo: 'texto', placeholder: 'XVIII Colóquio Brasileiro de Matemática', col: 6 },
    { chave: 'periodo',     rotulo: 'PERÍODO DO EVENTO, EXAME OU DEFESA',        tipo: 'texto', placeholder: '22 a 26 de julho de 2024', col: 6 },
    { chave: 'cidade_evento', rotulo: 'CIDADE DO EVENTO, EXAME OU DEFESA',       tipo: 'texto', placeholder: 'Rio de Janeiro', col: 3 },
    { chave: 'estado_evento', rotulo: 'ESTADO DO EVENTO, EXAME OU DEFESA',       tipo: 'texto', placeholder: 'RJ', col: 2 },
    { chave: 'pais_evento',   rotulo: 'PAÍS DO EVENTO, EXAME OU DEFESA',         tipo: 'texto', placeholder: 'Brasil', col: 2 },
    { chave: 'link_evento',   rotulo: 'LINK DO EVENTO, EXAME OU DEFESA',         tipo: 'texto', placeholder: 'https://www.evento.org.br', opcional: true, col: 5 },
    { chave: 'valor',         rotulo: 'VALOR SOLICITADO (R$)',                   tipo: 'moeda', placeholder: '1500', col: 3 },
    { chave: 'detalhamento',  rotulo: 'DETALHAMENTO DO PEDIDO',                  tipo: 'texto', placeholder: 'Solicito auxílio para custeio de transporte, hospedagem e alimentação durante o evento.', multilinea: true, col: 6 },
    { chave: 'apresentacao',  rotulo: 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', tipo: 'select', opcoes: ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'], col: 3 }
  ];

  var CAMPOS_ENDERECO = [
    { chave: 'nascimento', rotulo: 'DATA DE NASCIMENTO', tipo: 'data', placeholder: '01021980', col: 2 },
    { chave: 'logradouro', rotulo: 'LOGRADOURO',         tipo: 'texto', placeholder: 'Rua do Matão', col: 3 },
    { chave: 'numero',     rotulo: 'NÚMERO',             tipo: 'texto', placeholder: '1010', col: 1 },
    { chave: 'complemento', rotulo: 'COMPLEMENTO',       tipo: 'texto', placeholder: 'Apto 42', opcional: true, col: 2 },
    { chave: 'bairro',     rotulo: 'BAIRRO',             tipo: 'texto', placeholder: 'Cidade Universitária', col: 2 },
    { chave: 'cep',        rotulo: 'CEP',                tipo: 'cep',   placeholder: '05508090', col: 2 },
    { chave: 'cidade',     rotulo: 'CIDADE',             tipo: 'texto', placeholder: 'São Paulo', col: 2 },
    { chave: 'estado',     rotulo: 'ESTADO',             tipo: 'texto', placeholder: 'SP', col: 1 }
  ];

  var CAMPOS_PAGAMENTO = [
    { chave: 'cpf',       rotulo: 'CPF (SEPARADOS POR PONTOS E TRAÇO)',     tipo: 'cpf',   placeholder: '12345678909', col: 2 },
    { chave: 'rg',        rotulo: 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', tipo: 'texto', placeholder: '12.345.678-9', col: 2 },
    { chave: 'banco',     rotulo: 'NOME DO BANCO',                          tipo: 'texto', placeholder: 'Banco do Brasil', col: 3 },
    { chave: 'agencia',   rotulo: 'NÚMERO DA AGÊNCIA',                      tipo: 'texto', placeholder: '0123', col: 2 },
    { chave: 'conta',     rotulo: 'NÚMERO DA CONTA',                        tipo: 'texto', placeholder: '12345-6', col: 3 }
  ];

  var BLOCOS = function (aba) {
    var solicitante = CAMPOS_SOLICITANTE_BASE.slice();
    if (aba === 'alunos') {
      solicitante = solicitante.concat(CAMPOS_SOLICITANTE_ALUNOS);
    }
    return [
      { titulo: 'SOLICITANTE E EVENTO', campos: solicitante.concat(CAMPOS_EVENTO) },
      { titulo: 'ENDEREÇO DO SOLICITANTE', campos: CAMPOS_ENDERECO },
      { titulo: 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO', campos: CAMPOS_PAGAMENTO }
    ];
  };

  var FORMATADORES = {
    moeda: function (v) {
      var d = v.replace(/\D/g, '').replace(/^0+(?=\d)/, '');
      if (!d) return '';
      var cents = parseInt(d, 10);
      return 'R$ ' + cents.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    },
    cpf: function (v) {
      var d = v.replace(/\D/g, '').slice(0, 11);
      var out = d.slice(0, 3);
      if (d.length >= 4) out += '.' + d.slice(3, 6);
      if (d.length >= 7) out += '.' + d.slice(6, 9);
      if (d.length >= 10) out += '-' + d.slice(9, 11);
      return out;
    },
    cep: function (v) {
      var d = v.replace(/\D/g, '').slice(0, 8);
      if (d.length >= 6) return d.slice(0, 5) + '-' + d.slice(5, 8);
      return d;
    },
    data: function (v) {
      var d = v.replace(/\D/g, '').slice(0, 8);
      var out = d.slice(0, 2);
      if (d.length >= 3) out += '/' + d.slice(2, 4);
      if (d.length >= 5) out += '/' + d.slice(4, 8);
      return out;
    }
  };

  function montaFormulario(form, aba) {
    var blocos = BLOCOS(aba);
    for (var b = 0; b < blocos.length; b++) {
      var bloco = document.createElement('section');
      bloco.className = 'bloco';
      var titulo = document.createElement('h2');
      titulo.textContent = blocos[b].titulo;
      bloco.appendChild(titulo);
      var grade = document.createElement('div');
      grade.className = 'campos';
      bloco.appendChild(grade);
      var campos = blocos[b].campos;
      for (var c = 0; c < campos.length; c++) {
        grade.appendChild(montaCampo(campos[c]));
      }
      form.appendChild(bloco);
    }
    var botao = document.createElement('button');
    botao.type = 'submit';
    botao.className = 'botao';
    botao.textContent = 'Enviar solicitação';
    form.appendChild(botao);
  }

  function montaCampo(cfg) {
    var wrap = document.createElement('div');
    wrap.className = 'campo c' + cfg.col;
    var label = document.createElement('label');
    label.textContent = cfg.rotulo;
    var id = 'f-' + cfg.chave;
    label.setAttribute('for', id);
    wrap.appendChild(label);
    var controle;
    if (cfg.tipo === 'select') {
      controle = document.createElement('select');
      var vazio = document.createElement('option');
      vazio.value = '';
      vazio.textContent = cfg.placeholder || 'Selecione...';
      controle.appendChild(vazio);
      for (var i = 0; i < cfg.opcoes.length; i++) {
        var o = document.createElement('option');
        o.value = cfg.opcoes[i];
        o.textContent = cfg.opcoes[i];
        controle.appendChild(o);
      }
    } else if (cfg.multilinea) {
      controle = document.createElement('textarea');
      controle.rows = 4;
      controle.placeholder = cfg.placeholder;
    } else {
      controle = document.createElement('input');
      controle.type = 'text';
      controle.placeholder = cfg.placeholder;
      if (cfg.tipo !== 'texto') {
        controle.setAttribute('inputmode', 'numeric');
        controle.dataset.tipoFormato = cfg.tipo;
        controle.addEventListener('blur', function (e) {
          var fn = FORMATADORES[e.target.dataset.tipoFormato];
          if (fn) e.target.value = fn(e.target.value);
        });
      }
    }
    controle.id = id;
    controle.name = cfg.chave;
    wrap.appendChild(controle);
    return wrap;
  }

  function coletar(form) {
    var dados = {};
    var el = form.elements;
    for (var i = 0; i < el.length; i++) {
      var campo = el[i];
      if (campo.name) dados[campo.name] = campo.value.trim();
    }
    return dados;
  }

  function mostraErros(panel, erros) {
    panel.innerHTML = '';
    for (var i = 0; i < erros.length; i++) {
      var linha = document.createElement('div');
      linha.className = 'erro-mensagem';
      linha.textContent = erros[i];
      panel.appendChild(linha);
    }
  }

  async function enviar(form, aba, panel, telaFormulario) {
    var dados = coletar(form);
    dados.aba = aba;
    var corpo = new URLSearchParams(dados);
    var resp;
    try {
      resp = await fetch('/solicitacao', { method: 'POST', body: corpo });
    } catch (e) {
      mostraErros(panel, ['Falha de comunicação com o servidor.']);
      return;
    }
    var json = await resp.json();
    if (resp.ok && !json.erro) {
      document.getElementById('oficio').textContent = json.oficio;
      telaFormulario.classList.add('escondido');
      document.getElementById('tela-confirmacao').classList.remove('escondido');
      window.scrollTo(0, 0);
    } else {
      mostraErros(panel, json.erros || []);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var telaFormulario = document.getElementById('tela-formulario');
    var painelErro = { alunos: document.getElementById('alunos-erros'), docentes: document.getElementById('docentes-erros') };
    var formAlunos = document.getElementById('form-alunos');
    var formDocentes = document.getElementById('form-docentes');

    montaFormulario(formAlunos, 'alunos');
    montaFormulario(formDocentes, 'docentes');

    var abas = document.querySelectorAll('.aba');
    abas.forEach(function (aba) {
      aba.addEventListener('click', function () {
        var alvo = aba.dataset.alvo;
        abas.forEach(function (outra) {
          var ativa = outra === aba;
          outra.classList.toggle('ativa', ativa);
          outra.setAttribute('aria-selected', ativa ? 'true' : 'false');
        });
        formAlunos.classList.toggle('escondido', alvo !== 'alunos');
        formDocentes.classList.toggle('escondido', alvo !== 'docentes');
      });
    });

    formAlunos.addEventListener('submit', function (e) {
      e.preventDefault();
      enviaAsync(formAlunos, 'alunos', painelErro.alunos, telaFormulario);
    });
    formDocentes.addEventListener('submit', function (e) {
      e.preventDefault();
      enviaAsync(formDocentes, 'docentes', painelErro.docentes, telaFormulario);
    });

    function enviaAsync(form, aba, panel, tela) {
      mostraErros(panel, []);
      enviar(form, aba, panel, tela);
    }

    document.getElementById('botao-voltar').addEventListener('click', function () {
      document.getElementById('tela-confirmacao').classList.add('escondido');
      telaFormulario.classList.remove('escondido');
      window.scrollTo(0, 0);
    });
  });
})();
