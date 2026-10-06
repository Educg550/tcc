document.addEventListener('DOMContentLoaded', function() {
    var tabs = document.querySelectorAll('.tab');
    var contents = document.querySelectorAll('.tab-content');
    var forms = document.querySelectorAll('form');
    var errosBox = document.getElementById('erros');

    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            contents.forEach(function(c) { c.classList.remove('active'); });
            this.classList.add('active');
            document.getElementById(this.getAttribute('data-target')).classList.add('active');
            errosBox.hidden = true;
            document.getElementById('confirmacao').classList.remove('active');
            document.getElementById('form-alunos').classList.add('active');
            document.getElementById('form-docentes').classList.add('active');
        });
    });

    var inputsFormat = document.querySelectorAll('.autoformat');
    inputsFormat.forEach(function(input) {
        input.addEventListener('blur', function() {
            var val = this.value.replace(/\D/g, '');
            var nome = this.name;
            if (nome === 'valor') {
                var cents = val.padStart(3, '0');
                var dec = cents.slice(-2);
                var int = cents.slice(0, -2);
                if (int.length === 0) int = '0';
                this.value = 'R$ ' + parseInt(int, 10).toLocaleString('pt-BR') + ',' + dec;
            } else if (nome === 'cpf') {
                val = val.substring(0, 11);
                if (val.length > 0) this.value = val.replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})\.(\d{3})(\d)/, '$1.$2.$3').replace(/(\d{3})\.(\d{3})\.(\d{3})(\d)/, '$1.$2.$3-$4');
            } else if (nome === 'cep') {
                val = val.substring(0, 8);
                if (val.length > 0) this.value = val.replace(/(\d{5})(\d)/, '$1-$2');
            } else if (nome === 'data_nascimento') {
                val = val.substring(0, 8);
                if (val.length > 0) this.value = val.replace(/(\d{2})(\d)/, '$1/$2').replace(/(\d{2})\/(\d{2})(\d)/, '$1/$2/$3');
            }
        });
    });

    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var aba = form.id.replace('form-', '');
            var fd = new FormData(form);
            var dados = {};
            for (var [k, v] of fd.entries()) {
                dados[k] = v;
            }

            fetch('/api/solicitar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ aba: aba, dados: dados })
            })
            .then(function(res) {
                return res.json();
            })
            .then(function(res) {
                if (res.status === 'erro') {
                    var html = '';
                    res.erros.forEach(function(er) {
                        html += '<p>' + er + '</p>';
                    });
                    errosBox.innerHTML = html;
                    errosBox.hidden = false;
                } else {
                    errosBox.hidden = true;
                    form.classList.remove('active');
                    document.querySelector('.tab.active').classList.remove('active');
                    var conf = document.getElementById('confirmacao');
                    conf.classList.add('active');
                    document.getElementById('texto-oficio').textContent = res.oficio;
                }
            });
        });
    });
});
