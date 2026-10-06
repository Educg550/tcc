document.addEventListener('DOMContentLoaded', function () {
    const abaAlunos = document.getElementById('aba-alunos');
    const abaDocentes = document.getElementById('aba-docentes');
    const formAlunos = document.getElementById('form-alunos');
    const formDocentes = document.getElementById('form-docentes');
    const errosAlunos = document.getElementById('erros-alunos');
    const errosDocentes = document.getElementById('erros-docentes');
    const mainForm = document.getElementById('main-form');
    const mainConfirmacao = document.getElementById('main-confirmacao');
    const oficioEl = document.getElementById('oficio');

    // Alternância de abas
    function ativarAba(aba) {
        const ehAlunos = aba === abaAlunos;
        abaAlunos.classList.toggle('ativa', ehAlunos);
        abaAlunos.setAttribute('aria-selected', ehAlunos ? 'true' : 'false');
        abaDocentes.classList.toggle('ativa', !ehAlunos);
        abaDocentes.setAttribute('aria-selected', !ehAlunos ? 'true' : 'false');
        formAlunos.classList.toggle('oculto', !ehAlunos);
        formDocentes.classList.toggle('oculto', ehAlunos);
    }

    abaAlunos.addEventListener('click', function () { ativarAba(abaAlunos); });
    abaDocentes.addEventListener('click', function () { ativarAba(abaDocentes); });

    // Formatação de campos
    function soDigitos(valor) {
        return valor.replace(/\D/g, '');
    }

    function formataMoeda(valor) {
        const digitos = soDigitos(valor);
        if (!digitos) return '';
        const centavos = digitos;
        const inteiro = Math.floor(parseInt(centavos, 10) / 100).toLocaleString('pt-BR');
        const frac = String(parseInt(centavos, 10) % 100).padStart(2, '0');
        return 'R$ ' + inteiro + ',' + frac;
    }

    function formataCPF(valor) {
        const d = soDigitos(valor).slice(0, 11);
        let r = d.slice(0, 3);
        if (d.length > 3) r += '.' + d.slice(3, 6);
        if (d.length > 6) r += '.' + d.slice(6, 9);
        if (d.length > 9) r += '-' + d.slice(9, 11);
        return r;
    }

    function formataCEP(valor) {
        const d = soDigitos(valor).slice(0, 8);
        if (d.length <= 5) return d;
        return d.slice(0, 5) + '-' + d.slice(5);
    }

    function formData(valor) {
        const d = soDigitos(valor).slice(0, 8);
        let r = d.slice(0, 2);
        if (d.length > 2) r += '/' + d.slice(2, 4);
        if (d.length > 4) r += '/' + d.slice(4, 8);
        return r;
    }

    // Aplica formatação ao sair do campo (blur)
    function configurarFormatacao(form) {
        form.querySelector('[name="valor"]').addEventListener('blur', function () {
            this.value = formataMoeda(this.value);
        });
        form.querySelector('[name="cpf"]').addEventListener('blur', function () {
            this.value = formataCPF(this.value);
        });
        form.querySelector('[name="cep"]').addEventListener('blur', function () {
            this.value = formataCEP(this.value);
        });
        form.querySelector('[name="data_nascimento"]').addEventListener('blur', function () {
            this.value = formData(this.value);
        });
    }

    configurarFormatacao(formAlunos);
    configurarFormatacao(formDocentes);

    // Envio
    function mostraErros(container, erros) {
        container.innerHTML = '';
        erros.forEach(function (msg) {
            const p = document.createElement('p');
            p.textContent = msg;
            container.appendChild(p);
        });
    }

    function enviar(event, tipo, form, errosContainer) {
        event.preventDefault();
        const dados = {};
        new FormData(form).forEach(function (valor, chave) {
            dados[chave] = valor;
        });
        fetch('/api/solicitar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tipo: tipo, dados: dados })
        })
            .then(function (res) { return res.json(); })
            .then(function (res) {
                if (res.ok) {
                    mainForm.classList.add('oculto');
                    mainConfirmacao.classList.remove('oculto');
                    oficioEl.textContent = res.oficio;
                } else {
                    mostraErros(errosContainer, res.erros);
                }
            });
    }

    formAlunos.addEventListener('submit', function (e) {
        enviar(e, 'alunos', formAlunos, errosAlunos);
    });

    formDocentes.addEventListener('submit', function (e) {
        enviar(e, 'docentes', formDocentes, errosDocentes);
    });
});
