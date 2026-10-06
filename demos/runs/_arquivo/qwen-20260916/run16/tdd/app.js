document.addEventListener('DOMContentLoaded', () => {
  
  // Máscaras
  function formatCep(value) {
    const digits = value.replace(/\D/g, '');
    if (digits.length > 5) {
      return digits.slice(0, 5) + '-' + digits.slice(5, 8);
    }
    return digits;
  }

  function formatCpf(value) {
    const digits = value.replace(/\D/g, '');
    if (digits.length > 3 && digits.length <= 6) {
      return digits.slice(0, 3) + '.' + digits.slice(3);
    } else if (digits.length > 6 && digits.length <= 9) {
      return digits.slice(0, 3) + '.' + digits.slice(3, 6) + '.' + digits.slice(6);
    } else if (digits.length > 9) {
      return digits.slice(0, 3) + '.' + digits.slice(3, 6) + '.' + digits.slice(6, 9) + '-' + digits.slice(9, 11);
    }
    return digits;
  }

  function formatData(value) {
    const digits = value.replace(/\D/g, '');
    if (digits.length > 2 && digits.length <= 4) {
      return digits.slice(0, 2) + '/' + digits.slice(2);
    } else if (digits.length > 4) {
      return digits.slice(0, 2) + '/' + digits.slice(2, 4) + '/' + digits.slice(4, 8);
    }
    return digits;
  }

  function formatValor(value) {
    const digits = value.replace(/\D/g, '');
    if (!digits) return '';
    const cents = parseInt(digits, 10);
    return 'R$ ' + cents.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function applyMask(input, formatter) {
    input.addEventListener('blur', function () {
      if (this.name === 'valor') {
         this.value = formatter(this.value).replace(/\s/g, ''); // Remove espaço de R$ para facilitar parsing no JS se necessário
         this.value = formatter(this.value); 
      } else {
         this.value = formatter(this.value);
      }
    });
  }

  document.querySelectorAll('input[name="cep"]').forEach(i => applyMask(i, formatCep));
  document.querySelectorAll('input[name="cpf"]').forEach(i => applyMask(i, formatCpf));
  document.querySelectorAll('input[name="data_nascimento"]').forEach(i => applyMask(i, formatData));
  document.querySelectorAll('input[name="valor"]').forEach(i => applyMask(i, formatValor));

  // Abas
  const tabs = document.querySelectorAll('input[name="aba"]');
  tabs.forEach(tab => {
    tab.addEventListener('change', function () {
      document.getElementById('form-alunos').style.display = 'none';
      document.getElementById('form-docentes').style.display = 'none';
      document.getElementById('confirmacao').style.display = 'none';
      
      document.getElementById('form-' + this.value).style.display = 'block';
    });
  });

  // Envio
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      
      const abaInput = document.querySelector('input[name="aba"]:checked');
      const aba = abaInput ? abaInput.value : 'alunos';
      
      const dados = { aba: aba };
      
      this.querySelectorAll('input, select, textarea').forEach(el => {
         let val = el.value.trim();
         if (el.name === 'valor') {
             const digits = val.replace(/\D/g, '');
             val = digits ? parseInt(digits, 10).toString() : "";
         }
         dados[el.name] = val;
      });

      try {
        const resp = await fetch('/solicitacao', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(dados)
        });

        const res = await resp.json();
        const errosDiv = document.getElementById('erros-' + aba);
        errosDiv.innerHTML = '';
        
        if (res.erros) {
          res.erros.forEach(err => {
            const span = document.createElement('span');
            span.textContent = err;
            errosDiv.appendChild(span);
          });
        } else if (res.oficio) {
          document.getElementById('form-' + aba).style.display = 'none';
          document.getElementById('confirmacao').style.display = 'block';
          document.getElementById('oficio').textContent = res.oficio;
        }
      } catch (err) {
         console.error(err);
      }
    });
  });
});
