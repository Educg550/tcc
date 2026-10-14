from fastapi_mail import ConnectionConfig, FastMail
from pydantic import BaseModel
from src.settings import get_settings


class SendEmailResponse(BaseModel):
    message: str
    email_sent: str

def get_mail_builder():
    settings = get_settings()

    use_credentials = False
    if settings.SMTP_PASSWORD:
        use_credentials = True

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.FROM_EMAIL,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_SERVER,
        MAIL_STARTTLS=settings.SMTP_USE_TLS,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=use_credentials,
    )
    return FastMail(conf)

def footer():
    return """
<br/>
<p>Saudações universitárias,</p>

<p>Comissão de Seleção de Mestrado - Comissão Coordenadora</p>
<p>Programa de Mestrado em Ciência da Computação</p>
<p>Instituto de Matemática, Estatística e Ciência da Computação</p>
<p>Universidade de São Paulo</p>
"""