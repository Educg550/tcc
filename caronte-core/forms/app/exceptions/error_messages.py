from flask_babel import _

# generic
def ERROR():
    return _("Ocorreu uma falha")

def TIMEOUT():
    return _("Tempo de processamento esgotado")

# forms
def FORM_NOT_FOUND():
    return _("Ocorreu uma falha ao carregar o formulário")

def ERROR_CREATE_FORM():
    return _("Ocorreu uma falha ao criar o formulário")

def ERROR_REQUIRED_FIELDS(field):
    return _("Campo \"%(field)s\" requerido não foi preenchido", field=field)


def INVALID_FIELDS(field):
    return _("Campo \"%(field)s\" é inválido", field=field)

def CREATED_FORM():
    return _("Formulário foi criado com sucesso")

def ERROR_SUBMIT_FORM():
    return _("Ocorreu uma falha ao inserir o formulário")

def REMOVED_FORM():
    return _("Formulário removido com sucesso")

def INVALID_INPUT():
    return _("Valores de entrada incorretos")

def SUBMIT_FORM():
    return _("Sua resposta foi registrada")

## token
def ERROR_UPDATE_TOKEN():
    return _("Ocorreu uma falha ao atualizar o token")

def ERROR_TOKEN():
    return _("O token não é válido")

def TOKEN_UNAVAILABLE():
    return _("O token não está disponível no momento")

def CREATED_TOKEN():
    return _("Token criado com sucesso")

# files messages
def NO_FILE_PART():
    return _("Nenhuma parte do arquivo encontrada")

def FILE_NOT_FOUND():
    return _("Nenhum arquivo selecionado")

def FILE_ERROR():
    return _("Ocorreu uma falha com o arquivo")

def POSITION_FILE_ERROR(pos, line, col):
    return _("Posição %(pos)s, Linha %(line)s, Coluna %(col)s", pos=pos, line=line, col=col)

# identity
def IDENTITY_ERROR():
    return _("Ocorreu um problema durante a autenticação")

def IDENTITY_PERMISSION_DENIED():
    return _("Você não tem permissões suficientes para acessar esta página")

# email
def EMAIL_ERROR():
    return _("Ocorreu uma falha ao enviar o e-mail")

def SUBMIT_EMAIL():
    return _("E-mail enviado com sucesso")