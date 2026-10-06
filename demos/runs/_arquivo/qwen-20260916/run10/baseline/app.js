(function () {
  // ---------- Abas ----------
  const abaBtns = document.querySelectorAll('.aba');
  abaBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      abaBtns.forEach(function (b) {
        b.classList.remove('aba--ativa');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('aba--ativa');
      btn.setAttribute('aria-selected', 'true');
      var alvo = btn.dataset.aba;
      document.getElementById('form-alunos').classList.toggle('form-aba--visivel', alvo === 'alunos');
      document.getElementById('form-docentes').classList.toggle('form-aba--visivel', alvo === 'docentes');
    });
  });

  // ---------- Máscaras (formata ao sair do campo) ----------
  function digitos(v) { return v.replace(/\D/g, ''); }

  function mascaraCPF(v) {
    var d = digitos(v).slice(0, 11);
    if (d.length > 9) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6, 9) + '-' + d.slice(9);
    if (d.length > 6) return d.slice(0, 3) + '.' + d.slice(3, 6) + '.' + d.slice(6);
    if (d.length > 3) return d.slice(0, 3) + '.' + d.slice(3);
    return d;
  }

  function mascaraCEP(v) {
    var d = digitos(v).slice(0, 8);
    if (d.length > 5) return d.slice(0, 5) + '-' + d.slice(5);
    return d;
  }

  function mascaraData(v) {
    var d = digitos(v).slice(0, 8);
    if (d.length > 4) return d.slice(0, 2) + '/' + d.slice(2, 4) + '/' + d.slice(4);
    if (d.length > 2) return d.slice(0, 2) + '/' + d.slice(2);
    return d;
  }

  function mascaraMoeda(v) {
    var d = digitos(v).replace(/^0+/, '');
    if (!d) return '';
    var inteiro, centavos;
    if (d.length <= 2) { inteiro = 0; centavos = d; }
    else { centavos = d.slice(-2); inteiro = d.slice(0, -2); }
    while (centavos.length < 2) centavos = '0' + centavos;
    var partes = [];
    while (inteiro.length > 3) {
      partes.unshift(inteiro.slice(-3));
      inteiro = inteiro.slice(0, -3);
    }
    partes.unshift(inteiro);
    return 'R$ ' + partes.join('.') + ',' + centavos;
  }

  function aplicarMascara(input, fn) {
    input.addEventListener('blur', function () { input.value = fn(input.value); });
  }

  function conectarMascara(id, fn) {
    var el = document.getElementById(id);
    if (el) aplicarMascara(el, fn);
  }

  conectarMascara('al_valor', mascaraMoeda);
  conectarMascara('dc_valor', mascaraMoeda);
  conectarMascara('al_cpf', mascaraCPF);
  conectarMascara('dc_cpf', mascaraCPF);
  conectarMascara('al_cep', mascaraCEP);
  conectarMascara('dc_cep', mascaraCEP);
  conectarMascara('al_data', mascaraData);
  conectarMascara('dc_data', mascaraData);

  // ---------- Envio ----------
  function coletarDados(form) {
    var dados = {};
    form.querySelectorAll('[name]').forEach(function (el) {
      dados[el.name] = el.value;
    });
    return dados;
  }

  function abaAtual() {
    return document.querySelector('.aba--ativa').dataset.aba;
  }

  function mostrarErros(formId, erros) {
    var box = document.getElementById('erros-' + formId);
    box.innerHTML = '';
    if (erros.length > 0) {
      box.classList.add('erros--visivel');
      erros.forEach(function (e) {
        var p = document.createElement('p');
        p.textContent = e;
        box.appendChild(p);
      });
    } else {
      box.classList.remove('erros--visivel');
    }
  }

  function configurarForm(id) {
    document.getElementById(id).addEventListener('submit', async function (e) {
      e.preventDefault();
      var formId = id.replace('form-', '');
      var aba = abaAtual();
      var resp = await fetch('/solicitacao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aba: aba, dados: coletarDados(this) }),
      });
      var resultado = await resp.json();
      if (resultado.ok) {
        document.getElementById('tela-formulario').hidden = true;
        document.getElementById('tela-oficio').hidden = false;
        document.getElementById('oficio-texto').textContent = resultado.oficio;
      } else {
        mostrarErros(formId, resultado.erros);
      }
    });
  }

  configurarForm('form-alunos');
  configurarForm('form-docentes');
})();
