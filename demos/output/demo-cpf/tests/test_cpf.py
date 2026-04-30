import pytest
from cpf import validar_cpf


class TestCPFValidos:
    """Testes para CPFs válidos conhecidos."""

    def test_cpf_valido_exemplo_529_982_247_25(self):
        """CPF válido: 529.982.247-25."""
        assert validar_cpf("529.982.247-25") is True

    def test_cpf_valido_exemplo_111_444_777_35(self):
        """CPF válido: 111.444.777-35."""
        assert validar_cpf("111.444.777-35") is True


class TestCPFComTodosDigitosIguais:
    """Testes para CPFs com todos os dígitos iguais (sempre inválidos)."""

    def test_cpf_todos_zeros(self):
        """CPF com todos dígitos iguais a 0: 000.000.000-00."""
        assert validar_cpf("000.000.000-00") is False

    def test_cpf_todos_uns(self):
        """CPF com todos dígitos iguais a 1: 111.111.111-11."""
        assert validar_cpf("111.111.111-11") is False

    def test_cpf_todos_twos(self):
        """CPF com todos dígitos iguais a 2: 222.222.222-22."""
        assert validar_cpf("222.222.222-22") is False

    def test_cpf_todos_noves(self):
        """CPF com todos dígitos iguais a 9: 999.999.999-99."""
        assert validar_cpf("999.999.999-99") is False


class TestCPFFormatoIncorreto:
    """Testes para CPFs com formato incorreto."""

    def test_cpf_sem_pontuacao(self):
        """CPF sem pontos e hífen: 52998224725."""
        assert validar_cpf("52998224725") is False

    def test_cpf_com_apenas_traço(self):
        """CPF com apenas traço, sem pontos: 529982247-25."""
        assert validar_cpf("529982247-25") is False

    def test_cpf_com_apenas_pontos(self):
        """CPF com apenas pontos, sem traço: 529.982.247.25."""
        assert validar_cpf("529.982.247.25") is False

    def test_cpf_com_pontuacao_errada(self):
        """CPF com hífen no lugar de ponto: 529-982-247-25."""
        assert validar_cpf("529-982-247-25") is False

    def test_cpf_com_espacos(self):
        """CPF com espaços: 529 982 247 25."""
        assert validar_cpf("529 982 247 25") is False

    def test_cpf_com_caracteres_especiais(self):
        """CPF com caracteres especiais: 529@982@247#25."""
        assert validar_cpf("529@982@247#25") is False

    def test_cpf_vazio(self):
        """CPF vazio: string vazia."""
        assert validar_cpf("") is False

    def test_cpf_apenas_pontuacao(self):
        """CPF com apenas pontuação: ...-."""
        assert validar_cpf("...-") is False


class TestCPFNumeroDigitosIncorreto:
    """Testes para CPFs com número incorreto de dígitos."""

    def test_cpf_poucos_digitos(self):
        """CPF com poucos dígitos: 123.456.789-0."""
        assert validar_cpf("123.456.789-0") is False

    def test_cpf_muitos_digitos(self):
        """CPF com muitos dígitos: 123.456.789-090."""
        assert validar_cpf("123.456.789-090") is False

    def test_cpf_muito_poucos_digitos(self):
        """CPF com apenas 5 dígitos: 12.345-67."""
        assert validar_cpf("12.345-67") is False

    def test_cpf_muito_muitos_digitos(self):
        """CPF com 15 dígitos: 123.456.789.012-3456."""
        assert validar_cpf("123.456.789.012-3456") is False


class TestCPFDigitosVerificadoresIncorretos:
    """Testes para CPFs com dígitos verificadores incorretos."""

    def test_cpf_primeiro_verificador_incorreto(self):
        """CPF com primeiro verificador errado: 529.982.247-35."""
        assert validar_cpf("529.982.247-35") is False

    def test_cpf_segundo_verificador_incorreto(self):
        """CPF com segundo verificador errado: 529.982.247-24."""
        assert validar_cpf("529.982.247-24") is False

    def test_cpf_ambos_verificadores_incorretos(self):
        """CPF com ambos verificadores errados: 529.982.247-99."""
        assert validar_cpf("529.982.247-99") is False

    def test_cpf_verificador_incrementado(self):
        """CPF com verificadores incrementados: 123.456.789-10."""
        assert validar_cpf("123.456.789-10") is False

    def test_cpf_verificador_decrementado(self):
        """CPF com verificadores decrementados: 529.982.247-24."""
        assert validar_cpf("529.982.247-24") is False


class TestCPFCasosExtremos:
    """Testes para casos extremos."""

    def test_cpf_none(self):
        """Entrada None."""
        assert validar_cpf(None) is False

    def test_cpf_apenas_espacos(self):
        """CPF com apenas espaços em branco."""
        assert validar_cpf("   ") is False

    def test_cpf_com_letters(self):
        """CPF com letras: ABC.DEF.GHI-JK."""
        assert validar_cpf("ABC.DEF.GHI-JK") is False

    def test_cpf_com_letras_misturadas(self):
        """CPF com letras misturadas: 529.982.24A-25."""
        assert validar_cpf("529.982.24A-25") is False

    def test_cpf_com_letra_no_verificador(self):
        """CPF com letra no dígito verificador: 529.982.247-2X."""
        assert validar_cpf("529.982.247-2X") is False

    def test_cpf_negativo(self):
        """CPF com sinal negativo: -529.982.247-25."""
        assert validar_cpf("-529.982.247-25") is False

    def test_cpf_com_ponto_extra_inicio(self):
        """CPF com ponto extra no início: .529.982.247-25."""
        assert validar_cpf(".529.982.247-25") is False

    def test_cpf_com_ponto_extra_fim(self):
        """CPF com ponto extra no final: 529.982.247-25."""
        assert validar_cpf("529.982.247-25.") is False

    def test_cpf_com_dois_hifens(self):
        """CPF com dois hífens: 529.982.247--25."""
        assert validar_cpf("529.982.247--25") is False

    def test_cpf_com_hifen_inicio(self):
        """CPF com hífen no início: -529.982.247-25."""
        assert validar_cpf("-529.982.247-25") is False


class TestCPFCalculoDosVerificadores:
    """Testes específicos para validação dos dígitos verificadores usando a regra de módulo 11."""

    def test_cpf_111_444_777_35_calculo_correto(self):
        """Validar cálculo correto para 111.444.777-35.

        Primeiro verificador (posição 10):
        - Soma: 1*10 + 1*9 + 1*8 + 4*7 + 4*6 + 4*5 + 7*4 + 7*3 + 7*2
        - Soma: 10 + 9 + 8 + 28 + 24 + 20 + 28 + 21 + 14 = 162
        - 162 % 11 = 8
        - Verificador: 11 - 8 = 3 ✓

        Segundo verificador (posição 11):
        - Soma: 1*11 + 1*10 + 1*9 + 4*8 + 4*7 + 4*6 + 7*5 + 7*4 + 7*3 + 3*2
        - Soma: 11 + 10 + 9 + 32 + 28 + 24 + 35 + 28 + 21 + 6 = 204
        - 204 % 11 = 6
        - Verificador: 11 - 6 = 5 ✓
        """
        assert validar_cpf("111.444.777-35") is True

    def test_cpf_529_982_247_25_calculo_correto(self):
        """Validar cálculo correto para 529.982.247-25.

        Primeiro verificador (posição 10):
        - Soma: 5*10 + 2*9 + 9*8 + 9*7 + 8*6 + 2*5 + 2*4 + 4*3 + 7*2
        - Soma: 50 + 18 + 72 + 63 + 48 + 10 + 8 + 12 + 14 = 295
        - 295 % 11 = 9
        - Verificador: 11 - 9 = 2 ✓

        Segundo verificador (posição 11):
        - Soma: 5*11 + 2*10 + 9*9 + 9*8 + 8*7 + 2*6 + 2*5 + 4*4 + 7*3 + 2*2
        - Soma: 55 + 20 + 81 + 72 + 56 + 12 + 10 + 16 + 21 + 4 = 347
        - 347 % 11 = 6
        - Verificador: 11 - 6 = 5 ✓
        """
        assert validar_cpf("529.982.247-25") is True
