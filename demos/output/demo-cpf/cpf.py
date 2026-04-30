def validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF seguindo as regras matemáticas de módulo 11.

    Args:
        cpf: String no formato "XXX.XXX.XXX-YY"

    Returns:
        True se o CPF é válido, False caso contrário
    """
    # Validar entrada nula ou não é string
    if cpf is None or not isinstance(cpf, str):
        return False

    # Remover espaços em branco
    cpf = cpf.strip()

    # Validar formato exato: XXX.XXX.XXX-YY
    if len(cpf) != 14:  # 11 dígitos + 3 pontos + 1 hífen = 14 caracteres
        return False

    # Verificar estrutura de pontos e hífen
    if cpf[3] != '.' or cpf[7] != '.' or cpf[11] != '-':
        return False

    # Extrair apenas os dígitos
    digitos = cpf[0:3] + cpf[4:7] + cpf[8:11] + cpf[12:14]

    # Verificar se são todos dígitos
    if not digitos.isdigit():
        return False

    # Verificar se todos os dígitos são iguais (CPF inválido)
    if len(set(digitos)) == 1:
        return False

    # Extrair os 9 primeiros dígitos e os dois verificadores
    numeros = [int(d) for d in digitos]

    # Calcular primeiro dígito verificador
    # Multiplicar os 9 primeiros dígitos por 10, 9, 8, 7, 6, 5, 4, 3, 2
    soma1 = sum(numeros[i] * (10 - i) for i in range(9))
    resto1 = soma1 % 11

    # Se resto é 0 ou 1, o verificador é 0; senão é 11 - resto
    if resto1 < 2:
        verificador1 = 0
    else:
        verificador1 = 11 - resto1

    # Verificar se o primeiro verificador está correto
    if verificador1 != numeros[9]:
        return False

    # Calcular segundo dígito verificador
    # Multiplicar os 9 primeiros dígitos + primeiro verificador por 11, 10, 9, 8, 7, 6, 5, 4, 3, 2
    soma2 = sum(numeros[i] * (11 - i) for i in range(10))
    resto2 = soma2 % 11

    # Se resto é 0 ou 1, o verificador é 0; senão é 11 - resto
    if resto2 < 2:
        verificador2 = 0
    else:
        verificador2 = 11 - resto2

    # Verificar se o segundo verificador está correto
    if verificador2 != numeros[10]:
        return False

    return True
