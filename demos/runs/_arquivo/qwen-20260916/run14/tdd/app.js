document.addEventListener('DOMContentLoaded', function() {
    // Tab system
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');
    const main = document.getElementById('app-main');
    const confirmacao = document.getElementById('confirmacao');
    const tabsDiv = document.querySelector('.tabs');
    const headerMain = document.querySelector('main > header'); // not used, just reference
    
    let abaAtiva = 'ALUNOS';

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            abaAtiva = tab.getAttribute('data-tab');
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            contents.forEach(c => {
                if (c.id === abaAtiva) {
                    c.style.display = 'block';
                } else {
                    c.style.display = 'none';
                }
            });
            
            tabsDiv.style.display = 'flex';
            contents.forEach(c => c.style.display = 'none');
            document.getElementById(abaAtiva).style.display = 'block';
            confirmacao.style.display = 'none';
        });
    });

    // Masks
    const aplicarMascara = () => {
        document.querySelectorAll('[data-mask]').forEach(input => {
            input.addEventListener('blur', function() {
                const tipo = this.getAttribute('data-mask');
                let valor = this.value.replace(/\D/g, '');
                
                if (!valor) return;

                if (tipo === 'valor') {
                    let inteiro = parseInt(valor) / 100;
                    let inteiroStr = inteiro.toFixed(2).replace(/\./, ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
                    this.value = 'R$ ' + inteiroStr;
                } else if (tipo === 'cpf') {
                    this.value = valor.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
                } else if (tipo === 'cep') {
                    this.value = valor.replace(/(\d{5})(\d{3})/, "$1-$2");
                } else if (tipo === 'data') {
                    this.value = valor.replace(/(\d{2})(\d{2})(\d{4})/, "$1/$2/$3");
                }
            });
        });
    };
    aplicarMascara();

    // Form submission
    document.getElementById('form-alunos').addEventListener('submit', function(e) {
        e.preventDefault();
        enviarFormulario('ALUNOS');
    });

    document.getElementById('form-docentes').addEventListener('submit', function(e) {
        e.preventDefault();
        enviarFormulario('DOCENTES');
    });

    function enviarFormulario(aba) {
        const form = document.getElementById(aba === 'ALUNOS' ? 'form-alunos' : 'form-docentes');
        const errosDiv = document.getElementById(aba + '-erros');
        errosDiv.innerHTML = '';

        const dados = { aba: aba };
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            let id = input.id.split('-')[1];
            let val = input.value;
            if (input.getAttribute('data-mask') === 'valor') {
                val = val.replace(/\D/g, '');
                if (val === '0') val = '0'; // Pass raw string for backend
            }
            dados[id] = val;
        });

        fetch('/solicitacao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        })
        .then(r => r.json())
        .then(res => {
            if (res.erros && res.erros.length > 0) {
                res.erros.forEach(err => {
                    const p = document.createElement('p');
                    p.className = 'error-msg';
                    p.textContent = err;
                    errosDiv.appendChild(p);
                });
            } else if (res.oficio) {
                tabsDiv.style.display = 'none';
                contents.forEach(c => c.style.display = 'none');
                document.querySelector('#app-main > header').style.display = 'none';
                confirmacao.style.display = 'block';
                document.getElementById('oficio-texto').textContent = res.oficio;
            }
        });
    }
});
