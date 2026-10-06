document.addEventListener('DOMContentLoaded', function() {
  const abas = document.querySelectorAll('.aba');
  const formularios = {
    alunos: document.getElementById('form-alunos'),
    docentes: document.getElementById('form-docentes')
  };
  const errosDiv = document.getElementById('erros');
  const confirmacao = document.getElementById('confirmacao');
  const oficio = document.getElementById('oficio');

  abas.forEach(function(aba) {
    aba.addEventListener('click', function() {
      abas.forEach(function(a) { a.classList.remove('ativa'); });
      aba.classList.add('ativa');
      Object.keys(formularios).forEach(function(nome) {
        formularios[nome].classList.toggle('ativo', nome === aba.dataset.aba);
      });
      errosDiv.classList.remove('visivel');
    });
  });

  function formatarValor(input) {
    input.addEventListener('blur', function() {
      const digitos = input.value.replace(/\D/g, '');
      if (!digitos) { input.value = ''; return; }
      const centavos = parseInt(digitos, 10);
      const reais = Math.floor(centavos / 100);
      const cent = centavos % 100;
      const reaisStr = reais.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      input.value = 'R$ ' + reaisStr + ',' + cent.toString().padStart(2, '0');
    });
  }

  function formatarCPF(input) {
    input.addEventListener('blur', function() {
      const digitos = input.value.replace(/\D/g, '').slice(0, 11);
      if (!digitos) { input.value = ''; return; }
      if (digitos.length === 11) {
        input.value = digitos.slice(0,3) + '.' + digitos.slice(3,6) + '.' + digitos.slice(6,9) + '-' + digitos.slice(9);
      }
    });
  }

  function formatarCEP(input) {
    input.addEventListener('blur', function() {
      const digitos = input.value.replace(/\D/g, '').slice(0, 8);
      if (!digitos) { input.value = ''; return; }
      if (digitos.length === 8) {
        input.value = digitos.slice(0,5) + '-' + digitos.slice(5);
      }
    });
  }

  function formatarData(input) {
    input.addEventListener('blur', function() {
      const digitos = input.value.replace(/\D/g, '').slice(0, 8);
      if (!digitos) { input.value = ''; return; }
      if (digitos.length === 8) {
        input.value = digitos.slice(0,2) + '/' + digitos.slice(2,4) + '/' + digitos.slice(4);
      }
    });
  }

  formatarValor(document.getElementById('valor'));
  formatarValor(document.getElementById('valorDoc'));
  formatarCPF(document.getElementById('cpf'));
  formatarCPF(document.getElementById('cpfDoc'));
  formatarCEP(document.getElementById('cep'));
  formatarCEP(document.getElementById('cepDoc'));
  formatarData(document.getElementById('dataNascimento'));
  formatarData(document.getElementById('dataNascDoc'));

  function enviar(form, aba) {
    form.addEventListener('submit', function(event) {
      event.preventDefault();
      const dados = { aba: aba, solicitante: {}, evento: {}, endereco: {}, dadosBancarios: {} };
      const elementos = form.querySelectorAll('input, select, textarea');
      elementos.forEach(function(el) {
        if (el.name === 'nomeCidade') dados.endereco.cidade = el.value;
        else if (el.name === 'nomeEstado') dados.endereco.estado = el.value;
        else if (['nome','nUsp','programa','nivel','tipoAuxilio','email'].includes(el.name)) dados.solicitante[el.name] = el.value;
        else if (['nomeEvento','periodo','cidade','estado','pais','link','valor','detalhamento','apresentacao'].includes(el.name)) dados.evento[el.name] = el.value;
        else if (['logradouro','numero','complemento','bairro','cep'].includes(el.name)) dados.endereco[el.name] = el.value;
        else if (['dataNascimento','cpf','rg'].includes(el.name)) dados[el.name] = el.value;
        else if (['banco','agencia','conta'].includes(el.name)) dados.dadosBancarios[el.name] = el.value;
      });
      fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      })
      .then(function(response) { return response.json(); })
      .then(function(data) {
        if (data.ok) {
          errosDiv.classList.remove('visivel');
          document.querySelector('.abas').style.display = 'none';
          Object.keys(formularios).forEach(function(nome) { formularios[nome].style.display = 'none'; });
          oficio.textContent = data.oficio;
          confirmacao.classList.remove('oculto');
        } else {
          errosDiv.innerHTML = data.erros.map(function(e) { return '<div>' + e + '</div>'; }).join('');
          errosDiv.classList.add('visivel');
        }
      });
    });
  }

  enviar(formularios.alunos, 'alunos');
  enviar(formularios.docentes, 'docentes');
});
