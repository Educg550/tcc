import datetime

from app.common.Result import Result
from app.entities.Section import Section
from app.exceptions.error_messages import ERROR
from app.entities.Form import Form
from app.entities.Field import Field
from app.entities.Options import Options

from app.services.form_service import create_form

def template_form(notice, year):
    """
    Esquema para formulário de aceite
    """
    return Form({
        "title": {
            "pt": "PPGCC IME-USP: Manifestação de aceite de vaga no programa de Mestrado 2026",
            "en": "PPGCC IME-USP: Statement of Acceptance of the 2026 Master’s Program Offer",
        },
        "description": {
            "pt": '''\
Selecione sua decisão quanto à vaga no programa de mestrado:
''',
            "en": '''\
Select your decision regarding the master's program offer:
''',
        },
        "created_at": datetime.datetime.today(),
        "sections": [
            Section({
                "fields": [
                    Field({
                        "name": "comments",
                        "label": {
                            "pt": "Observações",
                            "en": "Comments"
                        },
                        "description": {
                            "pt": "Use este campo caso deseje enviar alguma observação relacionada à sua decisão. \\n Você pode explicar o motivo da recusa, informar aspectos importantes sobre sua aceitação, ou registrar alguma dúvida ou situação relevante para a coordenação.",
                            "en": "Use this field if you would like to provide any remarks related to your decision. \\n You may explain the reason for declining, share important information regarding your acceptance, or record any questions or relevant situations for the coordination team."
                        },
                        "type": "LongText", 
                    }),
                    Field({
                        "name": "accept",
                        "label": {
                            "pt": "",
                            "en": ""
                        },
                        "type": "Radio",
                        "required": True, 
                        "description": {
                            "pt": '''
Ao selecionar a opção de "aceite" você confirma oficialmente seu interesse e compromisso em ingressar no programa. A coordenação entrará em contato para os próximos passos.
''',
                            "en": '''
By selecting the “accept” option, you officially confirm your interest and commitment to join the program. The coordination team will contact you with the next steps.
'''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Aceito a vaga.",
                                    "en": "I accept the position."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Não aceito a vaga.",
                                    "en": "I do not accept the position."
                                }
                            }),
                        ] 
                    }),
                ]
            })
        ],
        "tags": {
            "Edital": notice,
            "Ano": year,
            "Publico": "aprovados"
        },
        "metadata": {
            "__message__": "entered by the system"
        }
    })

def run(db, notice, year):
    result = Result(message=ERROR())
    
    form = template_form(notice, year)

    form_id = create_form(db, form)

    if not form_id.succeeded:
        return result.handler_error(form_id.message)

    return Result(form_id, message=f"Form created successfully. Recommender form_id is: {form_id.data}")
