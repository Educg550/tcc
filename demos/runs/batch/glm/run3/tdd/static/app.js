document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.aba');
    const formAlunos = document.getElementById('form-alunos');
    const formDocentes = document.getElementById('form-docentes');
    const errosDiv = document.getElementById('erros');
    const confirmacao = document.getElementById('confirmacao');
    const oficioPre = document.getElementById('oficio');
    let tipoAtivo = 'alunos';

    // Alternância de abas
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tipoAtivo = tab.dataset.tipo;
            tabs.forEach(t => {
                t.classList.toggle('ativa', t === tab);
                t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
            });
            formAlunos.classList.toggle('visivel', tipoAtivo === 'alunos');
            formDocentes.classList.toggle('visivel', tipoAtivo === 'docentes');
        });
    });

    // Formatação dinâmica
    function formatarMoeda(valor) {
        let digitos = valor.replace(/\D/g, '');
        if (!digitos) return '';
        digitos = parseInt(digitos, 10);
        const centavos = digitos % 100;
        const inteiro = Math.floor(digitos / 100);
        return 'R$ ' + inteiro.toLocaleString('pt-BR') + ',' + String(centavos).padStart(2, '0');
    }

    function formatarCPF(valor) {
        const d = valor.replace(/\D/g, '').slice(0, 11);
        return d.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, (m, a, b, c, e) => {
            let r = `${a}.${b}.${c}`;
            if (e) r += `-${e}`;
            return r;
        });
    }

    function formatarCEP(valor) {
        const d = valor.replace(/\D/g, '').slice(0, 8);
        return d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d;
    }

    function formatarData(valor) {
        const d = valor.replace(/\D/g, '').slice(0, 8);
        return d.length > 4 ? `${d.slice(0,2)}/${d.slice(2,4)}/${d.slice(4)}` : (d.length > 2 ? `${d.slice(0,2)}/${d.slice(2)}` : d);
    }

    [formAlunos, formDocentes].forEach(form => {
        form.querySelector('[name=valor]').addEventListener('blur', (e) => e.target.value = formatarMoeda(e.target.value));
        form.querySelector('[name=cpf]').addEventListener('blur', (e) => e.target.value = formatarCPF(e.target.value));
        form.querySelector('[name=cep]').addEventListener('blur', (e) => e.target.value = formatarCEP(e.target.value));
        form.querySelector('[name=data_nascimento]').addEventListener('blur', (e) => e.target.value = formatarData(e.target.value));

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            errosDiv.innerHTML = '';
            errosDiv.classList.remove('visivel');
            const dados = { tipo: form === formAlunos ? 'alunos' : 'docentes' };
            new FormData(form).forEach((v, k) => dados[k] = v);
            try {
                const resp = await fetch('/api/solicitacao', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dados)
                });
                const corpo = await resp.json();
                if (!resp.ok) {
                    const mensagens = corpo.detail ? corpo.detail.mensagens : corpo.erros;
                    errosDiv.innerHTML = '<ul>' + mensagens.map(m => `<li>${m}</li>`).join('') + '</ul>';
                    errosDiv.classList.add('visivel');
                    return;
                }
                form.classList.remove('visivel');
                document.querySelector('.abas').style.display = 'none';
                oficioPre.textContent = corpo.oficio;
                confirmacao.classList.add('visivel');
                confirmacao.hidden = false;
                document.querySelectorAll('.formulario').forEach(f => f.style.display = 'none');
            } catch (err) {
                console.error('Erro:', err);
            }
        });
    });
});
