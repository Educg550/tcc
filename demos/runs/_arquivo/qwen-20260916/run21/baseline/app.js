(function() {
    'use strict';

    // Tabs
    var tabButtons = document.querySelectorAll('.tab-btn');
    var tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var tab = btn.getAttribute('data-tab');
            tabButtons.forEach(function(b) { b.classList.toggle('active', b === btn); });
            tabContents.forEach(function(c) { c.classList.toggle('active', c.getAttribute('data-tab') === tab); });
            document.getElementById('error-box').style.display = 'none';
            document.getElementById('error-box').innerHTML = '';
        });
    });

    // Formatting helpers
    function onlyDigits(s) {
        return s.replace(/\D/g, '');
    }

    function formatMoney(digits) {
        if (!digits) return '';
        var n = parseInt(digits, 10);
        var reais = Math.floor(n / 100);
        var centavos = n % 100;
        var str = reais.toLocaleString('de-DE');
        return 'R$ ' + str + ',' + String(centavos).padStart(2, '0');
    }

    function formatCpf(digits) {
        var d = onlyDigits(digits).substring(0, 11);
        if (!d) return '';
        var r = d;
        r = r.replace(/(\d{3})(\d)/, '$1.$2');
        r = r.replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3');
        r = r.replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
        return r;
    }

    function formatCep(digits) {
        var d = onlyDigits(digits).substring(0, 8);
        if (d.length > 5) {
            return d.substring(0, 5) + '-' + d.substring(5);
        }
        return d;
    }

    function formatDate(digits) {
        var d = onlyDigits(digits).substring(0, 8);
        var r = d;
        if (r.length > 4) {
            r = r.replace(/(\d{2})(\d{2})(\d{1,4})/, '$1/$2/$3');
        } else if (r.length > 2) {
            r = r.replace(/(\d{2})(\d{1,2})/, '$1/$2');
        }
        return r;
    }

    // Attach formatting to inputs with a custom attribute
    var moneyInputs = document.querySelectorAll('[name="VALOR SOLICITADO (R$)"]');
    moneyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            var d = onlyDigits(input.value);
            input.value = formatMoney(d);
            input.dataset.digits = d;
        });
    });

    var cpfInputs = document.querySelectorAll('[name="CPF (SEPARADOS POR PONTOS E TRAÇO)"]');
    cpfInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            input.value = formatCpf(input.value);
        });
    });

    var cepInputs = document.querySelectorAll('[name="CEP"]');
    cepInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            input.value = formatCep(input.value);
        });
    });

    var dateInputs = document.querySelectorAll('[name="DATA DE NASCIMENTO"]');
    dateInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            input.value = formatDate(input.value);
        });
    });

    // Submit handlers
    function handleFormSubmit(form, aba) {
        return function(e) {
            e.preventDefault();

            var formData = {};
            var inputs = form.querySelectorAll('input[name], select[name], textarea[name]');

            inputs.forEach(function(input) {
                var name = input.name;
                if (name === 'VALOR SOLICITADO (R$)') {
                    formData[name] = input.dataset.digits || '';
                } else {
                    formData[name] = input.value;
                }
            });

            formData['aba'] = aba;

            fetch('/api/solicitacao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(function(response) {
                response.text().then(function(body) {
                    if (response.status === 200) {
                        showConfirmation(body);
                    } else {
                        showError(body);
                    }
                });
            })
            .catch(function(err) {
                console.error('Request failed:', err);
                showError('<div class="errors"><ul><li>Erro de conexão</li></ul></div>');
            });
        };
    }

    function showError(html) {
        var errorBox = document.getElementById('error-box');
        errorBox.innerHTML = html;
        errorBox.style.display = 'block';
    }

    function showConfirmation(html) {
        var confirmation = document.getElementById('confirmation');
        var confirmContent = document.getElementById('confirm-content');
        confirmContent.innerHTML = html;
        confirmation.style.display = 'block';
        var mainContent = document.getElementById('main-content');
        var tabs = mainContent.querySelector('.tabs');
        tabs.style.display = 'none';
        var forms = mainContent.querySelectorAll('.tab-content');
        forms.forEach(function(f) { f.style.display = 'none'; });
        errorBox.style.display = 'none';
    }

    var errorBox = document.getElementById('error-box');

    document.getElementById('form-alunos').addEventListener('submit', handleFormSubmit(document.getElementById('form-alunos'), 'ALUNOS'));
    document.getElementById('form-docentes').addEventListener('submit', handleFormSubmit(document.getElementById('form-docentes'), 'DOCENTES'));
})();
