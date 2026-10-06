(function () {
  'use strict';

  var abas = {
    alunos: document.getElementById('aba-alunos'),
    docentes: document.getElementById('aba-docentes')
  };
  var formularios = {
    alunos: document.getElementById('form-alunos'),
    docentes: document.getElementById('form-docentes')
  };
  var painelFormularios = document.getElementById('formularios');
  var painelConfirmacao = document.getElementById('confirmacao');

  function selecionarAba(nome) {
    Object.keys(formularios).forEach(function (chave) {
      formularios[chave].classList.toggle('oculto', chave !== nome);
      abas[chave].classList.toggle('ativa', chave === nome);
    });
  }

  abas.alunos.addEventListener('click', function () { selecionarAba('alunos'); });
  abas.docentes.addEventListener('click', function () { selecionarAba('docentes'); });

  function soDigitos(valor) {
    var saida = '';
    for (var i = 0; i < valor.length; i++) {
      var caractere = valor.charAt(i);
      if (caractere >= '0' && caractere <= '9') {
        saida += caractere;
      }
    }
    return saida;
  }

  function comMilhar(reais) {
    var fim = '';
    while (reais.length > 3) {
      fim = '.' + reais.slice(-3) + fim;
      reais = reais.slice(0, -3);
    }
    return reais + fim;
  }

  var formatadores = {
    moeda: function (valor) {
      var digitos = soDigitos(valor);
      if (!digitos) {
        return '';
      }
      var numero = parseInt(digitos, 10);
      var centavos = String(numero % 100);
      if (centavos.length < 2) {
        centavos = '0' + centavos;
      }
      return 'R$ ' + comMilhar(String(Math.floor(numero / 100))) + ',' + centavos;
    },
    cpf: function (valor) {
      var digitos = soDigitos(valor);
      if (digitos.length !== 11) {
        return valor;
      }
      return digitos.slice(0, 3) + '.' + digitos.slice(3, 6) + '.' + digitos.slice(6, 9) + '-' + digitos.slice(9);
    },
    cep: function (valor) {
      var digitos = soDigitos(valor);
      if (digitos.length !== 8) {
        return valor;
      }
      return digitos.slice(0, 5) + '-' + digitos.slice(5);
    },
    data: function (valor) {
      var digitos = soDigitos(valor);
      if (digitos.length !== 8) {
        return valor;
      }
      return digitos.slice(0, 2) + '/' + digitos.slice(2, 4) + '/' + digitos.slice(4);
    }
  };

  Object.keys(formatadores).forEach(function (classe) {
    var campos = document.querySelectorAll('.' + classe);
    for (var i = 0; i < campos.length; i++) {
      campos[i].addEventListener('blur', function () {
        this.value = formatadores[classe](this.value);
      });
    }
  });

  var CAMPOS = [
    'nome_completo',
    'n_usp',
    'programa',
    'email',
    'nome_evento',
    'periodo_evento',
    'cidade_evento',
    'estado_evento',
    'pais_evento',
    'link_evento',
    'valor_solicitado',
    'detalhamento',
    'apresentacao',
    'data_nascimento',
    'logradouro',
    'numero',
    'complemento',
    'bairro',
    'cep',
    'cidade',
    'estado',
    'cpf',
    'rg_rnm',
    'banco',
    'agencia',
    'conta'
  ];

  function coletar(form, aba) {
    var dados = { aba: aba };
    CAMPOS.forEach(function (nome) {
      dados[nome] = form.elements[nome].value.trim();
    });
    if (aba === 'alunos') {
      dados.nivel = form.elements['nivel'].value.trim();
      dados.tipo_auxilio = form.elements['tipo_auxilio'].value.trim();
    }
    return dados;
  }

  function mostrarErros(form, erros) {
    var caixa = form.querySelector('.erros');
    caixa.textContent = '';
    erros.forEach(function (mensagem) {
      var linha = document.createElement('p');
      linha.textContent = mensagem;
      caixa.appendChild(linha);
    });
    caixa.classList.remove('oculto');
  }

  function enviar(evento) {
    evento.preventDefault();
    var form = evento.target;
    var aba = form.getAttribute('data-aba');
    form.querySelector('.erros').classList.add('oculto');
    fetch('/api/solicitacao', {
      method: 'POST',
      headers: { 'Content-Type': 'application/' },
      body: JSON.stringify(coletar(form, aba))
    }).then(function (resposta) {
      return resposta.().then(function (corpo) {
        return { ok: resposta.ok, corpo: corpo };
      });
    }).then(function (resultado) {
      if (resultado.ok) {
        painelFormularios.classList.add('oculto');
        painelConfirmacao.classList.remove('oculto');
        document.getElementById('oficio').textContent = resultado.corpo.oficio;
      } else {
        mostrarErros(form, resultado.corpo.erros || ['Não foi possível registrar a solicitação.']);
      }
    });
  }

  formularios.alunos.addEventListener('submit', enviar);
  formularios.docentes.addEventListener('submit', enviar);
})();
