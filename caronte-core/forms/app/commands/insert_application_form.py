import csv
import datetime

from app.common.Result import Result
from app.common.validators import email_regex
from app.entities.Options import Options
from app.entities.Section import Section
from app.exceptions.error_messages import ERROR

from app.entities.Form import Form
from app.entities.Field import Field

from app.logger import Logger
from app.services.form_service import create_form
from app.services.token_service import create_shared_token

csv_file_universities = "app/commands/application_submissions/universities.csv"
csv_file_courses = "app/commands/application_submissions/courses.csv"

# def check_if_exist_form(db, notice, year):
#     def iterable(cur):
#         x = cur.fetchone()

#         while x is not None:
#             if x[0] is not None and x[0]['Edital'] == notice and x[0]['Ano'] == year:
#                 return True
#             x = cur.fetchone()

#         return False

#     res = None
#     with db.transaction() as f:
#         res = f.sql(f"select tags from {TABLE_NAME_FORM}", callback=iterable)
#     return res

def template_form(notice, year):
    universities = []
    courses = []

    with open(csv_file_universities, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            universities.append(Options({
                "value": {
                    "pt": row["pt"],
                    "en": row["en"]
                }
            }))
    with open(csv_file_courses, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            courses.append(Options({
                "value": {
                    "pt": row["pt"],
                    "en": row["en"]
                }
            }))

    return Form({
        "title": {
            "pt": f"Inscrição no Programa de {notice.capitalize()} em Ciência da Computação (IME-USP {year})",
            "en": f"Application for the {notice.capitalize()}'s in Computer Science (MS-CC-IME-USP 2026)"
        },
        "created_at": datetime.datetime.today(),
        "sections": [
            Section({
                "description": {
                    "pt": f'''\
Este é o **formulário de inscrição no processo seletivo para {notice} em Ciência da Computação do Instituto de Matemática e Estatística da Universidade de São Paulo**, para ingresso em **{year}**. O formulário conta com 5 partes:\\n 
- Dados pessoais;\\n
- dados acadêmicos;\\n
- dados profissionais;\\n
- interesses de pesquisa e dados adicionais;\\n
- envio de documentos.\\n

Também é recomendado que você se informe apropriadamente sobre as [linhas de pesquisa do programa](https://www.ime.usp.br/dcc/areas-pesquisa) e seu interesse.
''',
                    "en": f'''\
This is **the application form for the {notice}'s in Computer Science program at the Institute of Mathematics and Statistics of the University of São Paulo**. The form has five parts:

- Personal information;\\n
- academic information;\\n
- professional information;\\n
- research interests and additional information;\\n
- document submission.\\n

It is also recommended that you familiarize yourself with the [program's research areas](https://www.ime.usp.br/dcc/areas-pesquisa) and your interests.
''',
                },
                "fields": [
                    Field({
                        "name": "acknowledgment",
                        "label": {
                            "pt": "Confirmação de ciência",
                            "en": "Acknowledgment"
                        },
                        "type": "CheckBox",
                        "required": True, 
                        "description": {
                            "pt": '''
Ao assinalar a caixa abaixo, você declara que está ciente e de acordo com os termos descritos no edital. Em particular, você se declarar ciente de que sua inscrição só será aceita após o preenchimento completo desse formulário e do envio dos documentos mencionados no edital estritamente dentro do prazo de inscrição. Possíveis atrasos devidos a infraestrutura computacional (incluindo a disponibilidade desse formulário online) ou ocorrências pessoais não alteram os prazos de submissão de documentos e formulário.
''',
                            "en": '''
By checking the box below, you declare that you acknowledge and agree to abide by all the regulations described in the call for applications. In particular, you declare that you are aware and agree that your  application will only be accepted if this form is properly filled, including the requested documents, within the due date. Delays caused by any lacking computational resources (this form availability included) and personal issues will not cause an extension of the deadlines.
'''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Estou ciente.",
                                    "en": "I acknowledge."
                                }
                            })
                        ] 
                    }),
                ]
            }),
            Section({
                "title": {
                    "pt": "Dados pessoais",
                    "en": "Personal Info"
                }, 
                "fields": [
                    Field({ 
                        "name": "fullname",
                        "label": {
                            "pt": "Nome Completo",
                            "en": "Full Name"
                        }, 
                        "type": "Text", 
                        "required": True 
                    }),
                    Field({ 
                        "name": "mother-fullname",
                        "label": {
                            "pt": "Nome Completo da mãe",
                            "en": "Mother's Full Name"
                        }, 
                        "type": "Text", 
                        "required": True 
                    }),
                    Field({ 
                        "name": "birth",
                        "label": {
                            "pt": "Data de Nascimento",
                            "en": "Date of Birth"
                        }, 
                        "type": "Date", 
                        "required": True 
                    }),
                    Field({ 
                        "name": "biological-sex",
                        "description": {
                            "pt": '''
*Esta informação é utilizada exclusivamente para integração com o sistema Janus.*
''',
                            "en": '''
*This information is used exclusively for integration with the Janus system.*
'''
                        },
                        "label": {
                            "pt": "Sexo biológico (conforme documentos oficiais)",
                            "en": "Biological sex (as stated in official documents)"
                        }, 
                        "type": "Radio",
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Feminino",
                                    "en": "Female"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Masculino",
                                    "en": "Male"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Prefiro não responder",
                                    "en": "Prefer not to answer"
                                }
                            })
                        ]
                    }),
                    Field({
                        "name": "nationality",
                        "label": {
                            "pt": "Nacionalidade",
                            "en": "Country of birth"
                        }, 
                        "type": "Text", 
                        "required": True 
                    }),
                    Field({
                        "name": "cpf",
                        "label": {
                            "pt": "Cadastro de Pessoa Física (CPF)",
                            "en": "CPF"
                        }, 
                        "type": "Text",
                        "description": {
                            "pt": "Obrigatório para cidadãos brasileiros",
                            "en": "Required for Brazilian citizens"
                        },
                    }),
                    Field({
                        "name": "type-official-document",
                        "label": {
                            "pt": "Tipo de documento oficial",
                            "en": "Type of Official Document"
                        },
                        "type": "Radio",
                        "description": {
                            "pt": "Selecione qual documento deseja informar",
                            "en": "Select which document you want to provide"
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Carteira de Identidade Nacional (CIN)",
                                    "en": "National Identity Card (CIN)"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Documento de identidade Estrangeiro",
                                    "en": "Foreign Identity Document"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Passaporte",
                                    "en": "Passport"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Protocolo de Registro Nacional de Estrangeiro",
                                    "en": "National Foreigner Registration Protocol"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Registro geral (RG)",
                                    "en": "General Registration (RG)"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "RNE",
                                    "en": "RNM"
                                }
                            })
                        ] 
                    }),
                    Field({
                        "name": "document-number",
                        "label": {
                            "pt": "Número do documento",
                            "en": "Document Number"
                        }, 
                        "type": "Text",
                        "description": {
                            "pt": "Informe o número do documento selecionado acima",
                            "en": "Enter the number of the document selected above"
                        },
                    }),
                    Field({
                        "name": "official-document-file",
                        "label": {
                            "pt": "Anexar documento oficial",
                            "en": "Attach official document"
                        }, 
                        "type": "File",
                        "required": True, 
                        "description": {
                            "pt": "Anexe uma cópia digitalizada do seu documento oficial",
                            "en": "Attach a scanned copy of your official document"
                        },
                    }),
                    Field({
                        "name": "nusp",
                        "label": {
                            "pt": "Número usp (se realizado)",
                            "en": "USP Number (if taken)"
                        }, 
                        "type": "Text",
                        "description": {
                            "pt": '''
Informe o seu número USP (se você já foi aluno da USP). Caso não possua, deixe em branco.
''',
                            "en": '''
Enter your USP student number if you were previously enrolled at USP. Leave blank if you don’t have one.
'''
                        },
                    }),
                    Field({ 
                        "name": "phone-number",
                        "description": {
                            "pt": "*usado para entrar em contato caso seja necessário complementar alguma informação*",
                            "en": "*used to contact you if any additional information is required*"
                        },
                        "label": {
                            "pt": "Número de telefone",
                            "en": "Phone Number"
                        }, 
                        "placeholder": "(XX) XXXX-XXXX",
                        "type": "Text", 
                        "required": True 
                    }),
                    Field({
                        "name": "address",
                        "label": {
                            "pt": "Endereço atual",
                            "en": "Place of residence"
                        }, 
                        "type": "Text", 
                        "required": True,
                        "description": {
                            "pt": "Escreva seu endereço de residência completo com cidade, estado e país",
                            "en": "Current place of residence including city, state/region and country"
                        },
                    }),
                    Field({
                        "name": "website",
                        "label": {
                            "pt": "Página profissional",
                            "en": "Professional page"
                        }, 
                        "type": "Text",
                        "description": {
                            "pt": '''
Endereço de página profissional, como LinkedIn, currículo online ou portfólio.\\n

*Não incluir perfis pessoais de redes sociais*
''',
                            "en": '''
Professional webpage address, such as LinkedIn, online CV, or portfolio.\\n

*Do not include personal social media profiles.*
'''
                        },
                    }),
                    Field({
                        "name": "disabilities",
                        "label": {
                            "pt": "Pessoa portadora de deficiência",
                            "en": "Person with Disabilities"
                        }, 
                        "type": "CheckBox",
                        "description": {
                            "pt": '''
Declaração de autoidentificação como pessoa portadora de deficiência (PCD). O preenchimento dessa questão é opcional.
''',
                            "en": '''
Declaration of self-identification as a person with disabilities. The data is collected for supporting summary statistics reports.
'''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Declaro que me identifico como PCD.",
                                    "en": "I identify as a person with disability."
                                }
                            })
                        ] 
                    }),
                    Field({
                        "name": "disabilities-file",
                        "label": {
                            "pt": "Laudo médico comprobatório (PCD grave)",
                            "en": "Medical Certificate (Severe Disability - PCD)"
                        }, 
                        "type": "File",
                        "description": {
                            "pt": '''
Envie o laudo médico que comprove sua condição de deficiência grave, conforme a Lei Brasileira de Inclusão da Pessoa com Deficiência (Lei nº 13.146/2015). \\n

*Este envio é obrigatório apenas para candidatos que se identificam como PCD grave.*
''',
                            "en": '''
Please upload a medical certificate proving your condition of severe disability, in accordance with the Brazilian Law for the Inclusion of Persons with Disabilities (Law No. 13,146/2015).\\n

*This upload is required only for candidates who identify as having a severe disability (PCD).*
'''
                        },
                    }),
                    Field({
                        "name": "ethnicity-race",
                        "label": {
                            "pt": "Etnia e cor",
                            "en": "Ethnicity and Race Identification"
                        }, 
                        "type": "CheckBox",
                        "description": {
                            "pt": '''
Declaração de autoidentificação como pessoa preta, parda ou indígena (PPI). O preenchimento é opcional.
''',
                            "en": '''
Declaration of self-identification as a black, brown or Brazilian indigenous person. Providing this information is optional.
'''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Declaro que me identifico como PPI.",
                                    "en": "I identify as a black, brown or Brazilian indigenous person."
                                }
                            })
                        ] 
                    }),
                    Field({
                        "name": "ethnicity-race-file",
                        "label": {
                            "pt": "Comprovação de pertencimento indígena (certidão Funai)",
                            "en": "Proof of Indigenous Affiliation (Funai Certificate)"
                        }, 
                        "type": "File",
                        "description": {
                            "pt": '''
Envie a certidão expedida pela Funai que comprove seu pertencimento a uma tribo indígena.\\n 
*Este envio é obrigatório apenas para candidatos que se identificam como indígenas (PPI).*
''',
                            "en": '''
Please upload the certificate issued by Funai that proves your affiliation with an indigenous tribe.\\n

*This upload is required only for candidates who identify as Indigenous (PPI).*
'''
                        },
                    }),
                ]
            }),
            Section({
                "title": {
                    "pt": "Dados acadêmicos",
                    "en": "Academic Info"
                },
                "fields": [
                    Field({
                        "name": "lattes-cv",
                        "label": {
                            "pt": "Currículo Lattes",
                            "en": "Lattes CV"
                        }, 
                        "type": "Text",
                        "required": True, 
                        "prefix": "http://lattes.cnpq.br/",
                        "placeholder": "123456789",
                        "validation": r"^[\s]*[\d]+[\s]*$",
                        "description": {
                            "pt": '''
Endereço eletrônico para o seu currículo na [plataforma Lattes do CNPq](https://lattes.cnpq.br/), devidamente preenchido com informações pertinentes (formação acadêmica, experiências em pesquisa como IC, publicação de artigos, participação em escolas de verão, congressos acadêmicos etc);  Caso você não tenha ainda um currículo na plataforma Lattes, cadastre um novo currículo e preencha-o como indicado acima.                  
''',
                            "en": '''
Web address of your academic curriculum in the [Lattes platform](https://lattes.cnpq.br/). You should create an account and fill out the important details such as academic history, research experiences, publications, etc. 
        '''
                        },
                    }),
                    Field({
                        "name": "lattes-cv-file",
                        "label": {
                            "pt": "Cópia do currículo Lattes",
                            "en": "Copy of Your Lattes CV"
                        }, 
                        "type": "File",
                        "required": True, 
                        "description": {
                            "pt": '''
Arquivo PDF do seu currículo Lattes devidamente preenchido. Use a opção `"imprimir"` para gerar um documento legível. No evento das informações contidas neste arquivo diferirem das informações disponíveis no currículo Lattes online (acessado através do endereço fornecido no item anterior), serão consideradas as informações contidas neste documento.                  
''',
                            "en": '''
Upload a PDF copy of your Lattes CV - this copy will be considered as the official information provided.
'''
                        },
                    }),
                    Field({
                        "name": "course-of-graduation",
                        "label": {
                            "pt": "Curso de graduação",
                            "en": "Course of Graduation"
                        }, 
                        "type": "Text",
                        "required": True,
                        "options": courses,
                        "description": {
                            "pt": '''
Responder com curso de graduação mais recente caso tenha se graduado mais de uma vez.\\n
*A lista de preenchimento automático apresenta apenas algums cursos; você não precisa se limitar às opções sugeridas.*
''',
                            "en": '''
If you have more than one degree, answer with the most recent graduation.\\n
*The autocomplete list shows only some courses; you do not need to limit yourself to the suggested options.*                            
'''
                        },
                    }),
                    Field({
                        "name": "year-of-graduation",
                        "label": {
                            "pt": "Ano de graduação",
                            "en": "Year of Graduation"
                        }, 
                        "placeholder": "YYYY",
                        "validation": r"\d{4}",
                        "type": "Text",
                        "error_message": {
                            "pt": "Este campo apenas aceita anos válidos",
                            "en": "This field only accepts valid years"
                        },
                        "required": True, 
                        "description": {
                            "pt": "Ano de obtenção do diploma de graduação informado no item anterior",
                            "en": "Year of graduation as informed in the previous item."
                        },
                    }),
                    Field({
                        "name": "institution",
                        "label": {
                            "pt": "Instituição de ensino de graduação",
                            "en": "Institution where you obtained your undergraduate degree"
                        }, 
                        "options": universities,
                        "type": "Text",
                        "required": True, 
                        "placeholder": "Universidade de São Paulo (USP)",
                        "description": {
                            "pt": '''
Nome completo da instituição onde você obteve sua graduação, conforme resposta no item anterior.\\n
*A lista de preenchimento automático apresenta apenas algumas instituições; você não precisa se limitar às opções sugeridas.*
''',
                            "en": '''
Name of the institution from where you graduated (as responded in the previous item).\\n
*The autocomplete list shows only some institutions; you are not required to select from the suggested options.*                            
'''
                        },
                    }),
                    Field({
                        "name": "country-undergraduate",
                        "label": {
                            "pt": "País da instituição de ensino da graduação",
                            "en": "Country of Undergraduate Degree"
                        }, 
                        "type": "Text",
                        "required": True, 
                        "placeholder": "Brasil",
                        "description": {
                            "pt": "País no qual sua graduação foi obtida.",
                            "en": "Country where you acquired your undergraduate degree."
                        },
                    }),
                    Field({
                        "name": "studies-transcripts",
                        "label": {
                            "pt": "Histórico escolar de graduação",
                            "en": "Undergraduate Studies Transcripts"
                        }, 
                        "type": "File",
                        "required": True, 
                        "description": {
                            "pt": "Cópia digitalizada do seu histórico oficial de graduação, com as disciplinas cursadas e as respectivas avaliações.",
                            "en": "Digital copy of you academic transcripts."
                        },
                    }),
                    Field({
                        "name": "year-poscomp",
                        "label": {
                            "pt": "Ano de realização do POSCOMP (se realizado)",
                            "en": "Year of POSCOMP Exam (if taken)"
                        }, 
                        "placeholder": "YYYY",
                        "validation": r"\d{4}",
                        "type": "Text",
                        "error_message": {
                            "pt": "Este campo apenas aceita anos válidos",
                            "en": "This field only accepts valid years"
                        },
                        "description": {
                            "pt": '''
Informe o ano em que você realizou o exame do [POSCOMP](https://www.sbc.org.br/poscomp/). Se você fez mais de uma vez, escolha o ano do exame que deseja utilizar. Se não fez o exame, pule a questão 
''',
                            "en": '''
If you have taken the [POSCOMP](https://www.sbc.org.br/poscomp/) exam, inform the year. If you have taken the exame more than once, inform the year whose grades you wish to use. Skip this question if you have not taken the exam.
'''
                        },
                    }),
                    Field({
                        "name": "grades-poscomp",
                        "label": {
                            "pt": "Nota no POSCOMP (se realizado)",
                            "en": "Grades in the POSCOMP Exam (if available)"
                        }, 
                        "type": "Number",
                        "description": {
                            "pt": '''
Pontuação total no exame [POSCOMP](https://www.sbc.org.br/poscomp/) conforme respondido no item anterior. Se você fez o exame esse ano mas ainda não possui a nota, deixe em branco. Se você não realizou o exame, pule essa questão  
''',
                            "en": '''
Total score in the [POSCOMP](https://www.sbc.org.br/poscomp/) exam, as informed in the previous item. If you have taken the exame but do not know your score, leave it blank. Skip this question if you have not taken the exam.
'''
                        },
                    }),
                    Field({
                        "name": "poscomp-file",
                        "label": {
                            "pt": "Relatório do POSCOMP, GRE ou equivalente, se houver",
                            "en": "POSCOMP or GRE report, or equivalent, if available"
                        }, 
                        "type": "File",
                    }),
                    Field({
                        "name": "graduate-courses-file",
                        "label": {
                            "pt": "Anexar certificado das disciplinas de Pós-Graduação na USP cursadas como aluno/a especial",
                            "en": "Graduate courses already taken at USP"
                        },
                        "description": {
                            "pt": '''
Anexe um arquivo PDF contendo o certificado das disciplinas de Pós-Graduação que você cursou na USP. Entre em contato com a coordenação de pós-graduação do seu instituto para solicitar o documento, por exemplo, se você for aluno do IME, contate [cpg@ime.usp.br](mailto:cpg@ime.usp.br).\\n

*Não anexe disciplinas cursadas fora da USP*; você pode mencioná-las na sua carta de apresentação, em seu currículo (lattes) ou como informações adicionais.                     
''',
                            "en": '''
Attach a PDF file containing the certificate of the Graduate courses you attended at USP. Contact the graduate program coordination of your institute to request the document; for example, if you are a student at IME, contact [cpg@ime.usp.br](mailto:cpg@ime.usp.br).\\n

*Do not attach courses taken outside USP*; you may mention them in your cover letter, in your CV (Lattes), or as additional information.
'''
                        },
                        "type": "File"
                    }),
                ]
            }),
            Section({
                "title": {
                    "pt": "Dados profissionais",
                    "en": "Professional Info"
                },
                "fields": [
                    Field({
                        "name": "current-job",
                        "label": {
                            "pt": "Última atividade remunerada",
                            "en": "Last professional position"
                        },
                        "description": {
                            "pt": '''
Caso esteja empregado no momento ou no passado recente, descreva a posição, empresa e tipo de trabalho. Deixe em branco caso não tenha tido trabalho remunerado recente ou não queira/possa compartilhar essa informação.

Exemplo: Desenvolvedor de Software Frontend, SuperTec Soluções, desde 2016 - Desenvolvendo soluções de software para clientes da empresa.                  
''',
                            "en": '''
If you are currently employed or have been in the recent past, describe the position, company, and type of work. Leave blank if you have not had recent paid work or do not wish/cannot share this information.

Example: Frontend Software Developer, SuperTec Solutions, since 2016 – Developing software solutions for the company’s clients.
'''
                        },
                        "type": "LongText"
                    })
                ]
            }),
            Section({
                "title": {
                    "pt": "Interesses de pesquisa",
                    "en": "Research Interests"
                },
                "fields": [
                    Field({
                        "name": "primary-area",
                        "label": {
                            "pt": "Área de interesse primária",
                            "en": "Primary Area of Interest"
                        },
                        "type": "Radio",
                        "required": True, 
                        "description": {
                            "pt": '''
        Sua candidatura será avaliada primordialmente dentro da área informada abaixo, de acordo com a quantidade de vagas informadas no edital e com os interesses de pesquisa dos orientadores do programa. Você pode acessar [https://www.ime.usp.br/dcc/areas-pesquisa](https://www.ime.usp.br/dcc/areas-pesquisa) para conhecer os docentes separados por linhas de pesquisa; recomenda-se fortemente que você entre em conhecimento com o trabalho dos docentes antes de escolher uma área. Uma forma de fazer isso é olhar o nome e as publicações do docente no Google Scholar (scholar.google.com). 
        ''',
                            "en": '''
        Your application will be analyzed according to the line of research informed below, following the number of vacancies informed at the Opening Call. You find a list of the researchers of the Programa, organized by research interest at the website [https://www.ime.usp.br/dcc/areas-pesquisa](https://www.ime.usp.br/dcc/areas-pesquisa). It is highly recommended that you select you area according to the interests of the researchers in the program.
        '''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Algoritmos, teoria dos grafos, otimização combinatória e teoria da computação.",
                                    "en": "Algorithms, Graph Theory, Combinatorial Optimization, Theoretical Computer Science."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Métodos numéricos de otimização linear e não-linear.",
                                    "en": "Computational Methods for Linear and Non-linear Optimization."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Aprendizado de máquina.",
                                    "en": "Machine Learning."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Ciência de dados.",
                                    "en": "Data Science."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Computação musical.",
                                    "en": "Computer Music"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Inteligência artificial.",
                                    "en": "Artificial Intelligence."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Métodos formais.",
                                    "en": "Formal Methods."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Visão computacional, interação humano-computador e processamento de imagens.",
                                    "en": "Computer Vision, Human-Computer Interaction, Image Processing."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Engenharia de software e bancos de dados.",
                                    "en": "Software Engineering and DataBase Systems"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Segurança de dados e criptografia.",
                                    "en": "Data Security and Cryptography."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Informática na educação.",
                                    "en": "Informatics in Education."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Redes de computadores, sistemas distribuídos e computação paralela.",
                                    "en": "Computer Networks, Distributed Systems and Parallel Computing."
                                }
                            })
                        ] 
                    }),
                    Field({
                        "name": "secondary-area",
                        "label": {
                            "pt": "Área de interesse secundária",
                            "en": "Secondary Area Of Interest"
                        },
                        "type": "Radio",
                        "description": {
                            "pt": '''
        Escolha uma área de interesse secundária; tal informação será usada apenas de maneira auxiliar. 
        ''',
                            "en": '''
        Choose your secondary area of interest; this information will be used only as additional information.
        '''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Algoritmos, teoria dos grafos, otimização combinatória e teoria da computação.",
                                    "en": "Algorithms, Graph Theory, Combinatorial Optimization, Theoretical Computer Science."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Ciência de dados e Aprendizado de máquina.",
                                    "en": "Data Science and Machine Learning."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Computação musical.",
                                    "en": "Computer Music"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Engenharia de software e bancos de dados.",
                                    "en": "Software Engineering and DataBase Systems"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Informática na educação.",
                                    "en": "Informatics in Education."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Inteligência artificial e métodos formais.",
                                    "en": "Artificial Intelligence and Formal Methods."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Métodos numéricos de otimização linear e não-linear.",
                                    "en": "Computational Methods for Linear and Non-linear Optimization."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Redes de computadores, sistemas distribuídos e computação paralela.",
                                    "en": "Computer Networks, Distributed Systems and Parallel Computing."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Segurança de dados e criptografia.",
                                    "en": "Data Security and Cryptography."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Visão computacional, interação humano-computador e processamento de imagens.",
                                    "en": "Computer Vision, Human-Computer Interaction, Image Processing."
                                }
                            })
                        ] 
                    }),
                    Field({
                        "name": "motivation-letter",
                        "label": {
                            "pt": "Carta de motivação",
                            "en": "Motivation Letter"
                        }, 
                        "type": "File",
                        "required": True, 
                        "description": {
                            "pt": '''
Texto objetivo contendo uma apresentação sucinta (máx. 3 páginas) e descrevendo os motivos da solicitação de ingresso no programa, suas experiências em pesquisa e atividades acadêmicas relevantes (iniciação científica, estágio em laboratório de pesquisa, participação em atividades de extensão ou aperfeiçoamento, trabalho de conclusão de curso etc), suas perspectivas em relação ao programa e sua carreira e seus interesses de pesquisa.                 
''',
                            "en": '''
Short text (max. 3 pages) describing the motivations of your application, your past research experience and relevant academic activities (research internship, specialization courses, final term projects, etc), your expectations towards the program and future career and your potential topics of research.
'''
                        },
                    }),
                    Field({
                        "name": "recommended-name-1",
                        "label": {
                            "pt": "Nome Completo do Primeiro de Recomendador",
                            "en": "Recommender 1’s Name"
                        }, 
                        "required": True, 
                        "type": "Text",
                        "description": {
                            "pt": '''
Informe o nome completo (ou como é conhecido profissionalmente) da pessoa que você indicará para escrever sua carta de recomendação. Certifique-se de que a pessoa está ciente e de acordo em fornecer a recomendação. O sistema enviará **automaticamente** um e-mail com instruções para que a carta seja submetida.\\n

Certifique-se de que os endereços de e-mail estão corretos antes de enviar.\\n

*Essa informação será vista pelo seu recomendador*
''',
                            "en": '''
Provide the full name (or professional name) of the person you are indicating to write a recommendation letter on your behalf. Make sure the person has agreed to write the letter. An **automatic** email with submission instructions will be sent to the recommender.\\n

Please ensure that the email addresses provided are accurate before submission.\\n

*This information will be seen by your recommender*
'''
                        },
                    }),
                    Field({
                        "name": "recommended-email-1",
                        "label": {
                            "pt": "E-mail institucional do Primeiro Recomendador",
                            "en": "Recommender 1’s Email"
                        }, 
                        "required": True, 
                        "validation": email_regex(),
                        "error_message": {
                            "pt": "Esse campo aceita apenas o formato de e-mail",
                            "en": "This field only accepts email format"
                        },
                        "type": "Text",
                        "description": {
                            "pt": "*Essa informação será vista pelo seu recomendador*",
                            "en": "*This information will be seen by your recommender*"
                        },
                    }),
                    Field({
                        "name": "recommended-name-2",
                        "label": {
                            "pt": "Nome Completo do Segundo de Recomendador",
                            "en": "Recommender 2’s Name"
                        }, 
                        "required": False, 
                        "type": "Text",
                        "description": {
                            "pt": "*Essa informação será vista pelo seu recomendador*",
                            "en": "*This information will be seen by your recommender*"
                        },
                    }),
                    Field({
                        "name": "recommended-email-2",
                        "label": {
                            "pt": "E-mail institucional do Segundo Recomendador",
                            "en": "Recommender 2’s Email"
                        }, 
                        "validation": email_regex(),
                        "error_message": {
                            "pt": "Esse campo aceita apenas o formato de e-mail",
                            "en": "This field only accepts email format"
                        },
                        "type": "Text",
                        "description": {
                            "pt": "*Essa informação será vista pelo seu recomendador*",
                            "en": "*This information will be seen by your recommender*"
                        },
                    })
                ]
            }),
            Section({
                "title": {
                    "pt": "Semestre pretendido e Grau de dedicação",
                    "en": "Intended Semester and Level of Commitment"
                },
                "fields": [
                    Field({
                        "name": "semester",
                        "label": {
                            "pt": "Você está se candidatando para iniciar no primeiro ou segundo semestre?",
                            "en": "Are you applying to start program in the first or second semester?"
                        },
                        "type": "Radio",
                        "description": {
                            "pt": '''
Dessa forma, você deve informar se está se candidatando para iniciar no primeiro ou segundo semestre. Note que no momento da matrícula você já deve ter concluído seu curso de graduação e ter colado grau.
''',
                            "en": '''
Accordingly, you must indicate whether you intend to start in the program in the first or second semester. Keep in mind that by the time of enrollment you must have a certified proof of the award of  your undergraduate degree (e.g., by an issued diploma).
'''
                        },
                        "required": True,
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Primeiro semestre.",
                                    "en": "First semester."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Segundo semestre.",
                                    "en": "Second semester."
                                }
                            }),
                        ] 
                    }),
                    Field({
                        "name": "intended-level",
                        "label": {
                            "pt": "Qual o seu grau pretendido de dedicação à pesquisa durante mestrado?",
                            "en": "What is your intended level of commitment to research during the program?"
                        },
                        "type": "Radio",
                        "description": {
                            "pt": '''
Um grau de comprometimento integral assume dedicação exclusiva e de pelo menos 40 horas semanais ao mestrado (disciplinas, pesquisa, etc). Caso você prevê uma ocupação com horários flexíveis ou carga horária reduzida, informe dedicação parcial.
''',
                            "en": '''
A Full-Time commitment implies at least 40-hour week dedication to the Graduate program (study and research). If you have some occupation with flexible working hours or reduced workload, please inform Part-Time commitment.
'''
                        },
                        "required": True,
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Integral e exclusiva (não vou desempenhar outras atividades).",
                                    "en": "Full-time (I will not have any other duties)."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Parcial e flexível (vou desempenhar outras atividades como trabalho remunerado, porém possuo flexibilidade de horário ou carga reduzida para realizar pesquisa e disciplinas).",
                                    "en": "Part-time, flexible (I will have other activities, such as paid job, but with flexibility or reduced workload to carry out my studies and research)."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Parcial (vou balancear meu trabalho em tempo integral com a pesquisa).",
                                    "en": "Part-time (I will balance my current job with my study and research)."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Não sei informar no momento.",
                                    "en": "I don't know yet."
                                }
                            }),
                        ] 
                    }),
                ]
            }),
            Section({
                "title": {
                    "pt": "Bolsa de estudos",
                    "en": "Scholarship"
                },
                "fields": [
                    Field({
                        "name": "scholarship",
                        "label": {
                            "pt": "Deseja concorrer a bolsa de estudos institucional (Capes ou CNPq)?",
                            "en": "Do you want to apply for an Institutional Scholarship?"
                        },
                        "type": "Radio",
                        "description": {
                            "pt": '''
A bolsa de estudos, se concedida, exige dedicação integral e exclusiva à pesquisa e reembolso dos valores recebidos em caso de desistência injustificada. 
''',
                            "en": '''
A limited number of institutional scholarships are available for full-time students. Those scholarships must be refunded in total in case the recipient fails to graduate without a proper justification.
'''
                        },
                        "options": [
                            Options({ 
                                "value": {
                                    "pt": "Sim",
                                    "en": "Yes"
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Não",
                                    "en": "No"
                                } 
                            }),
                        ] 
                    }),
                ]
            }),
            Section({
                "title": {
                    "pt": "Informações adicionais",
                    "en": "Additional Infot"
                },
                "fields": [
                    Field({
                        "name": "relevant-information",
                        "label": {
                            "pt": "Informações adicionais relevantes",
                            "en": "Extra Relevant Information"
                        },
                        "description": {
                            "pt": '''
        Escreva outras informações que você acha importante que sejam consideradas para sua aceitação em nosso programa, mas não foram informadas em itens anteriores. Não há necessidade de preencher esse campo.                  
        ''',
                            "en": '''
        If you feel that there is any information supporting your application that hasn't been informed previously, use the following space to provide it.
        '''
                        },
                        "type": "LongText"
                    }),
                    Field({
                        "name": "about-this-program",
                        "label": {
                            "pt": "Como ficou sabendo do programa de mestrado em Ciência da Computação do IME",
                            "en": "How did you know about this program?"
                        }, 
                        "type": "Text",
                        "description": {
                            "pt": '''
        Sua resposta é bem-vinda e nos ajuda a entender o alcance de nossas ações e melhorar o processo. 
        ''',
                            "en": '''
        We appreciate your feedback. This information helps us understanding how to better reach a broad audience and improve the admission process.
        '''
                        },
                    }),
                ]
            })
        ],
        "tags": {
            "Edital": notice,
            "Ano": year,
            "Publico": "candidatos"
        },
        "metadata": {
            "__message__": "entered by the system"
        }
    })

def run(db, notice, year):
    Result(message=ERROR())

    # exist = check_if_exist_form(db, notice, year)
    # if exist:
        # return result.handler_error(f"{notice.capitalize()} form of {year} has already been created.")

    form_schema = template_form(notice, year)

    form_id = create_form(db, form_schema)

    if not form_id.succeeded:
        Logger.print.error(form_id.message)
        return None

    token = create_shared_token(db, {
        "form_id": form_id.data,
        "unique_answers": True,
        "is_public": True,
    })

    return Result(str(token), message=f"Form created successfully. Token application form is: {token}")
