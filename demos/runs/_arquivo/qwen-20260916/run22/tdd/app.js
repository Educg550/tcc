document.addEventListener('DOMContentLoaded', () => {
  const tabAlunos = document.getElementById('tab-alunos');
  const tabDocentes = document.getElementById('tab-docentes');
  const formAlunos = document.getElementById('form-alunos');
  const formDocentes = document.getElementById('form-docentes');
  const formSection = document.getElementById('form-section');
  const confirmation = document.getElementById('confirmation');
  const oficio = document.getElementById('oficio');

  tabAlunos.addEventListener('click', () => {
    tabAlunos.classList.add('active');
    tabDocentes.classList.remove('active');
    formAlunos.classList.add('form-active');
    formAlunos.classList.remove('hidden');
    formDocentes.classList.add('hidden');
    formDocentes.classList.remove('form-active');
    document.getElementById('errors-alunos').classList.add('hidden');
  });

  tabDocentes.addEventListener('click', () => {
    tabDocentes.classList.add('active');
    tabAlunos.classList.remove('active');
    formDocentes.classList.add('form-active');
    formDocentes.classList.remove('hidden');
    formAlunos.classList.add('hidden');
    formAlunos.classList.remove('form-active');
    document.getElementById('errors-docentes').classList.add('hidden');
  });

  function formatCep(input) {
    let digits = input.value.replace(/\D/g, '').slice(0, 8);
    if (digits.length > 5) {
      input.value = digits.slice(0, 5) + '-' + digits.slice(5);
    } else {
      input.value = digits;
    }
  }

  function formatCpf(input) {
    let digits = input.value.replace(/\D/g, '').slice(0, 11);
    let val = '';
    for (let i = 0; i < digits.length; i++) {
      if (i === 3 || i === 6) val += '.';
      if (i === 9) val += '-';
      val += digits[i];
    }
    input.value = val;
  }

  function formatData(input) {
    let digits = input.value.replace(/\D/g, '').slice(0, 8);
    let val = '';
    for (let i = 0; i < digits.length; i++) {
      if (i === 2 || i === 4) val += '/';
      val += digits[i];
    }
    input.value = val;
  }

  function formatMoeda(input) {
    let digits = input.value.replace(/\D/g, '');
    if (!digits) return input.value = '';
    let cents = parseInt(digits, 10);
    let integer = Math.floor(cents / 100);
    let frac = cents % 100;
    let str = integer.toString();
    let formatted = '';
    for (let i = 0; i < str.length; i++) {
      if (i > 0 && (str.length - i) % 3 === 0) formatted += '.';
      formatted += str[i];
    }
    input.value = formatted + ',' + frac.toString().padStart(2, '0');
  }

  const fields = ['valor', 'data_nascimento', 'cep', 'cpf', 'valor_d', 'data_nascimento_d', 'cep_d', 'cpf_d'];
  fields.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('blur', function() {
        if (id === 'valor' || id === 'valor_d') formatMoeda(this);
        else if (id === 'data_nascimento' || id === 'data_nascimento_d') formatData(this);
        else if (id === 'cep' || id === 'cep_d') formatCep(this);
        else if (id === 'cpf' || id === 'cpf_d') formatCpf(this);
      });
    }
  });

  async function submitForm(form, tabName) {
    const data = new FormData(form);
    let obj = {};
    for (let [key, value] of data.entries()) {
      obj[key] = value;
    }

    const errorsBox = document.getElementById(`errors-${tabName}`);
    errorsBox.classList.add('hidden');

    try {
      const response = await fetch(`/solicitacao/${tabName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(obj)
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const result = await response.json();

      if (result.erros && result.erros.length > 0) {
        errorsBox.textContent = result.erros.join('\n');
        errorsBox.classList.remove('hidden');
      } else if (result.oficio) {
        oficio.textContent = result.oficio;
        formSection.classList.add('hidden');
        confirmation.classList.remove('hidden');
      }
    } catch (error) {
      console.error('Error:', error);
      errorsBox.textContent = 'Erro ao processar a solicitação.';
      errorsBox.classList.remove('hidden');
    }
  }

  formAlunos.addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm(formAlunos, 'alunos');
  });

  formDocentes.addEventListener('submit', function(e) {
    e.preventDefault();
    submitForm(formDocentes, 'docentes');
  });
});
