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
    Esquema para formulário da carta de recomendação
    """
    return Form({
        "title": {
            "pt": f"Formulário de Recomendação - {notice.capitalize()} em Ciência da Computação (IME-USP {year})",
            "en": f"Recommendation Form - {notice.capitalize()}'s in Computer Science (IME-USP {year})",
        },
        "description": {
            "pt": f'''\
*Para ser preenchido por quem está recomendando o(a) candidato(a).*

Este formulário permite a avaliação e recomendação de candidatura ao Programa de {notice.capitalize()} em Ciência da Computação do IME-USP. **Todas as informações fornecidas neste formulário são sigilosos para o/a candidato/a** e ajudam o processo de seleção de ingressantes no programa.
''',
            "en": f'''\
*To be completed by the person recommending the candidate.*

This form allows for the evaluation and recommendation of applications to the {notice.capitalize()}'s Program in Computer Science at IME-USP. **All information provided on this form is confidential to the candidate** and assists in the program selection process.
''',
        },
        "created_at": datetime.datetime.today(),
        "sections": [
            Section({
                "fields": [
                    Field({
                        "name": "fullname-candidate",
                        "label": {
                            "pt": "Nome completo do candidato a ser recomendado",
                            "en": "Full name of the candidate to be recommended"
                        }, 
                        "type": "Text", 
                        "required": True,
                        "disabled": True,
                    }),
                    Field({
                        "name": "fullname",
                        "label": {
                            "pt": "Nome completo",
                            "en": "Full name"
                        }, 
                        "type": "Text", 
                        "required": True,
                    })
                ],
            }),
            Section({
                "fields": [
                    Field({
                        "name": "affiliation",
                        "label": {
                            "pt": "Afiliação e posição atual",
                            "en": "Affiliation and current position"
                        }, 
                        "type": "Text",
                    }),
                    Field({
                        "name": "known-time",
                        "label": {
                            "pt": "Há quanto tempo conhece o candidato?",
                            "en": "How long have you known the candidate?"
                        }, 
                        "type": "Text",
                    }),
                    Field({
                        "name": "relationship",
                        "label": {
                            "pt": "Em quais contextos o conheceu?",
                            "en": "In what contexts did you meet him?"
                        },
                        "type": "CheckBox",
                        "description": {
                            "pt": "*Marque todos que se aplicam*",
                            "en": "*Check all that apply*"
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Orientador em programa de pós-graduação.",
                                    "en": "Advisor in Graduate Studies."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Orientador de Trabalho de Conclusão de Curso (TCC).",
                                    "en": "Advisor on undergraduate capstone project."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Orientador de Iniciação Científica (IC).",
                                    "en": "Supervisor in undergraduate research internship."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Ministrante de disciplina.",
                                    "en": "Teacher in University or College course."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Supervisor de monitoria.",
                                    "en": "Supervisor of Teaching Assistance."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Supervisor direto em emprego.",
                                    "en": "Direct supervisor at job."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Co-autoria em trabalho acadêmico.",
                                    "en": "Co-autorship in scientific work."
                                }
                            })
                        ] 
                    }),
                    Field({
                        "name": "rating",
                        "label": {
                            "pt": "Avaliação do candidato",
                            "en": "Candidate assessment"
                        },
                        "description": {
                            "pt": "Preencher com a avaliação das capacidades de aprendizado, comunicação, trabalho em equipe em relação a base de comparação (turma, grupo de estudo, orientandos etc).\\n Pode ser preenchido em Português, Inglês e Espanhol.",
                            "en": "Fill in with an assessment of learning, communication and teamwork capabilities in relation to the basis of comparison (class, study group, students, etc.).\\n It can be filled out in Portuguese, English, and Spanish."
                        },
                        "type": "LongText", 
                        "required": True
                    }),
                ]
            })
        ],
        "tags": {
            "Edital": notice,
            "Ano": year,
            "Publico": "recomendadores"
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
