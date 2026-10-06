document.addEventListener('DOMContentLoaded', () => {
  const abas = document.querySelectorAll('.aba');
  const forms = {
    alunos: document.getElementById('form-alunos'),
    docentes: document.getElementById('form-docentes')
  };
  const formArea = document.getElementById('form-area');
  const confirmArea = document.getElementById('confirm-area');
  const mensagemErro = document.getElementById('mensagens-erro');

  abas.forEach(aba => {
    aba.addEventListener('click', () => {
      abas.forEach(a => a.classList.remove('ativa'));
      aba.classList.add('ativa');

      Object.values(forms).forEach(f => f.classList.remove('ativa'));
      forms[aba.dataset.tab].classList.add('ativa');

      mensagemErro.classList.remove('visivel');
    });
  });

  const aplicarFormatacao = (input) => {
    const val = input.value;
    let digitos = val.replace(/\D/g, '');

    if (input.classList.contains('fmt-valor')) {
      if (!digitos) { input.value = ''; return; }
      let num = parseInt(digitos, 10);
      input.value = num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    } else if (input.classList.contains('fmt-cpf')) {
      let f = digitos.substring(0, 11);
      f = f.replace(/(\d{3})(\d{0,3})/, '$1.$2');
      f = f.replace(/(\d{3})\.(\d{3})(\d{0,3})/, '$1.$2.$3');
      f = f.replace(/(\d{3})\.(\d{3})\.(\d{0,3})(\d{0,2})/, '$1.$2.$3-$4');
      input.value = f;
    } else if (input.classList.contains('fmt-cep')) {
      input.value = digitos.substring(0, 8).replace(/(\d{5})(\d{0,3})/, '$1-$2');
    } else if (input.classList.contains('fmt-data')) {
      let f = digitos.substring(0, 8);
      f = f.replace(/(\d{2})(\d{0,2})/, '$1/$2');
      f = f.replace(/(\d{2})\/(\d{2})(\d{0,4})/, '$1/$2/$3');
      input.value = f;
    }
  };

  document.querySelectorAll('.fmt-valor, .fmt-cpf, .fmt-cep, .fmt-data').forEach(input => {
    input.addEventListener('blur', () => aplicarFormatacao(input));
  });

  Object.values(forms).forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      mensagemErro.classList.remove('visivel');

      const aba = form.id.split('-')[1];

      let dados = {
        nome: form.querySelector('[name=nome]').value,
        nusp: form.querySelector('[name=nusp]').value,
        programa: form.querySelector('[name=programa]').value,
        email: form.querySelector('[name=email]').value,
        evento: form.querySelector('[name=evento]').value,
        periodo: form.querySelector('[name=periodo]').value,
        cidade_evento: form.querySelector('[name=cidade_evento]').value,
        estado_evento: form.querySelector('[name=estado_evento]').value,
        pais_evento: form.querySelector('[name=pais_evento]').value,
        link: form.querySelector('[name=link]').value,
        valor: form.querySelector('[name=valor]').value,
        detalhamento: form.querySelector('[name=detalhamento]').value,
        apresentacao: form.querySelector('[name=apresentacao]').value,
        nascimento: form.querySelector('[name=nascimento]').value,
        logradouro: form.querySelector('[name=logradouro]').value,
        numero: form.querySelector('[name=numero]').value,
        complemento: form.querySelector('[name=complemento]').value,
        bairro: form.querySelector('[name=bairro]').value,
        cep: form.querySelector('[name=cep]').value,
        cidade: form.querySelector('[name=cidade]').value,
        estado: form.querySelector('[name=estado]').value,
        cpf: form.querySelector('[name=cpf]').value,
        rg: form.querySelector('[name=rg]').value,
        banco: form.querySelector('[name=banco]').value,
        agencia: form.querySelector('[name=agencia]').value,
        conta: form.querySelector('[name=conta]').value,
      };

      if (aba === 'alunos') {
        dados.nivel = form.querySelector('[name=nivel]').value;
        dados.tipo = form.querySelector('[name=tipo]').value;
      }

      try {
        const res = await fetch('/api/solicitar', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(dados)
        });

        const result = await res.json();

        if (res.status !== 200) {
          let errosHtml = '';
          result.erros.forEach(err => {
            errosHtml += `<div>${err}</div>`;
          });
          mensagemErro.innerHTML = errosHtml;
          mensagemErro.classList.add('visivel');
        } else {
          formArea.style.display = 'none';
          confirmArea.classList.add('visivel');
          document.getElementById('texto-oficio').textContent = result.oficio;
        }
      } catch (err) {
        mensagemErro.innerHTML = '<div>Ocorreu um erro no sistema.</div>';
        mensagemErro.classList.add('visivel');
      }
    });
  });
});