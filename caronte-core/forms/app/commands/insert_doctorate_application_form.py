import csv
import datetime

from app.common.Result import Result
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
                    "pt": '''\
Este é o formulário de inscrição no processo seletivo para doutorado no Programa de Pós-graduação em Ciência da Computação do Instituto de Matemática e Estatística da Universidade de São Paulo, para ingresso em 2026 em fluxo contínuo (as análises são realizadas em lote, em média, a cada 2 meses).

O formulário conta com 5 partes: Dados pessoais, dados acadêmicos, dados profissionais, interesses de pesquisa e dados adicionais. Além das perguntas colocadas, o preenchimento do formulário requer o envio dos seguintes documentos, em formato PDF: 

- Histórico escolar da graduação e pós-graduação (se aplicável),
- Texto da dissertação de mestrado ou de artigos publicados (se houver), 
- Cópia do currículo Lattes, 
- Carta de motivação.
- Plano de trabalho (somente para doutorado direto)
- Carta de anuência de orientador(a) (somente para doutorado direto)

Recomenda-se ter tais documentos devidamente preparados antes de iniciar o preenchimento do formulário, em especial a carta de motivação. O formulário também possibilita a informação de um possível orientador ou orientadora, caso seja a pessoa se candidatando seja aceita. Embora opcional, é altamente recomendável que candidatos prospectivos se familiarizem com os/as docentes orientadores/as do programa e, possivelmente, entre em contato previamente em vistas de uma possível orientação e definição de tema de pesquisa.
''',
                    "en": '''\
This is the application form for the Graduate Doctorate Program in Computer Science at the Institute of Mathematics and Statistics of the University of São Paulo. The form consists of a number of questions about contact information, academic performance, research interests and general information. In addition to the information provided, you will need to submit the following documents in pdf format:

- Transcripts of undergraduate and graduate (if existent) records,
- Manuscript of MSc Thesis or published scientific articles, if available
- Copy of your Lattes curriculum (see https://wwws.cnpq.br/cvlattesweb/pkg_cv_estr.inicio)
- Motivation letter
- Research plan (only for Direct-entry PhD)
- Letter of Acceptance from Supervisor (only for Direct-entry PhD)

If you are a non-Brazilian resident and intend to apply for the PhD program, we highly recommend you carefully read our website and contact the Graduate Office before starting your application. It is also highly advisable that you reach out for potential advisors first and agree on a research topic. 

At the present time, this form has only a Portuguese version.
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
Declaro que li e estou de acordo com todos os termos descritos no edital. Em particular, estou ciente de que minha inscrição só será aceita após o preenchimento completo desse formulário dentro do prazo de inscrição.''',
                            "en": '''
I declare that I have read and agree with all the terms described in the notice. In particular, I acknowledge that my application will only be accepted after this form has been completely filled within the application deadline.
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
            Section({"title":{
                "pt":   "Tipo de aplicação",
                "en":"Application Type"
    },
                    "fields":[
                        Field({"name":"application-type",
                        "label":{
                            "pt":"Tipo de aplicação",
                            "en":"Application type",
                        },
                               "description":{
                                   "pt":"O doutorado regular é restrito a pessoas com mestrado já concluído em Ciência da Computação ou em área correlata. Já o doutorado direto é direcionado a casos excepcionais de pessoas que não possuem mestrado, porém possuem capacidade comprovada de realização de pesquisa acadêmica (por exemplo, através da realização de iniciação científica, estágio em laboratório de pesquisa e/ou publicação de artigos). Note que os prazos e obrigações são diferentes para cada modalidade. Mais informações podem ser obtidas na página do programa https://www.ime.usp.br/pos-computacao/normas-programa/",
                                   "en":"The regular PhD is restricted to applicants holding a completed master's degree in Computer Science or a related area. The direct-entry PhD is aimed at exceptional cases without a master's degree but with proven research ability (for example, through undergraduate research, research internships and/or publications). Deadlines and obligations differ between modalities. More information at: https://www.ime.usp.br/pos-computacao/normas-programa/"
                                   },
                                    "type":"CheckBox",
                               "options":[
                                   Options({
                                       "value":{
                                           "pt":"Doutorado regular","en":"Regular PhD"
                                           }
                                       }),
                                   Options({
                                       "value":{
                                           "pt":"Doutorado direto","en":"Direct-entry PhD"
                                           }
                                       }),
                               ]},)
                    ]}),
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
                        "name": "birth",
                        "label": {
                            "pt": "Data de Nascimento",
                            "en": "Date of Birth"
                        }, 
                        "type": "Date", 
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
                        "name": "nationality",
                        "label": {
                            "pt": "Nacionalidade",
                            "en": "Country of birth"
                        }, 
                        "type": "Text", 
                        "required": True 
                    }),
                    Field({
                        "name":"type-and-document-number",
                        "label":{
                            "pt":"Tipo e no. de documento de identidade",
                            "en": "ID document type and number"
                        },
                        "description":{
                            "pt":"Exemplo: RG 12.345.678-9 ou Passaporte ABC123",
                            "en": "Example: RG 12.345.678-9 or Passport ABC123"
                        },
                        "type":"Text",
                        "required":True
                        }),
                    Field({
                        "name": "address",
                        "label": {
                            "pt": "Endereço atual",
                            "en": "Place of residence"
                        }, 
                        "type": "LongText", 
                        "required": True,
                        "description": {
                            "pt": "Exemplo: Rua do Matão 1010, Bloco CCSL, São Paulo, SP, Brasil",
                            "en": "Example: Rua do Matão 1010, CCSL Building, São Paulo, SP, Brazil"
                        },
                    }),
                    Field({ 
                        "name": "phone-number",
                        "description": {
                            "pt": "Recomendado para que possibilite um contato mais rápido, quando necessário:  DDD + número (se estrangeiro, DDI + número)",
                            "en": "Recommended to enable faster contact when necessary: area code + number (if foreign, country code + number)"
                        },
                        "label": {
                            "pt": "Número de telefone",
                            "en": "Phone Number"
                        }, 
                        "placeholder": "(XX) XXXX-XXXX",
                        "type": "Text", 
                        "required": False
                    }),
                    Field({
                        "name": "website",
                        "label": {
                            "pt": "Página pessoal",
                            "en": "Personal page"
                        }, 
                        "type": "Text",
                        "description": {
                            "pt":"Endereço de página pessoal com currículo ou portfólio ou página em site de relacionamento profissional (p.ex., Linked in)",
                            "en":"Personal page URL with your CV or portfolio, or a profile on a professional networking site (e.g., LinkedIn)"
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
Endereço eletrônico para o seu currículo na plataforma Lattes do CNPq (http://lattes.cnpq.br/número) devidamente preenchido com informações pertinentes (formação acadêmica, experiências em pesquisa como IC, publicação de artigos, participação em escolas de verão, congressos acadêmicos etc); é muito importante que você preencha corretamente e da forma mais completa possível. Caso você não tenha ainda um currículo na plataforma Lattes, cadastre um novo currículo e preencha-o como indicado acima.''',
                            "en": '''
Electronic address of your CV on the CNPq Lattes platform (http://lattes.cnpq.br/number), properly filled with relevant information (academic formation, research experience such as undergraduate research, publications, participation in summer schools, conferences, etc.). It is very important to provide this correctly and as completely as possible. If you do not yet have a Lattes CV, register and complete it as indicated above.
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
Arquivo pdf do seu currículo lattes devidamente preenchido. Use a opção 'imprimir' para gerar um documento legível. No evento das informações contidas neste arquivo diferirem das informações disponíveis no currículo lattes online (acessado através do endereço fornecido no item anterior), serão consideradas as informações contidas neste documento.
''',
                            "en": '''
PDF file of your completed Lattes CV. Use the 'print' option to generate a readable document. If the information in this uploaded file differs from the online Lattes CV (accessed via the address provided above), the uploaded document will be considered.
'''
                        },
                    }),
                    Field({
                        "name": "course-of-graduation",
                        "label": {
                            "pt": "Diploma(s) de graduação obtidos",
                            "en": "Undergraduate degree(s) obtained"
                        }, 
                        "type": "Text",
                        "required": True,
                        "description": {
                            "pt": '''
                                Título, instituição e ano de obtenção de diplomas de nível superior (graduação) obtidos

                                Exemplo: Bacharelado em Ciência da Computação, USP, 2018
                            ''',
                            "en": '''
Title, institution and year of undergraduate degrees obtained.

Example: Bachelor in Computer Science, USP, 2018
                            '''
                        },
                    }),
                    Field({
                        "name": "masters-degree-diploma",
                        "label":{
                            "pt":"Diploma de mestrado, se houver",
                            "en":"Master's degree diploma, if applicable"
                        },
                        "description":{
                            "pt":'''Título do diploma de mestrado, instituição e ano

                            Exemplo: Mestrado em Ciência da Computação, USP, 2018''',
                            "en":'''Title of the master's diploma, institution and year.

Example: Master's in Computer Science, USP, 2018'''
                        },
                        "type":"File"
                    }),
                    Field({
                        "name": "studies-transcripts",
                        "label": {
                            "pt": "Histórico escolar de graduação",
                            "en": "Undergraduate Studies Transcripts"
                        }, 
                        "type": "File",
                        "required": True, 
                        "description":{
                                "pt":"Cópia digitalizada do seu histórico oficial de graduação, com as disciplinas cursadas e as respectivas avaliações. ",
                                "en":"Scanned copy of your official undergraduate transcript, including courses taken and the respective grades."
                        }
                    }),
                    Field({
                        "name":"research-plan",
                        "label":{
                            "pt":"Plano de trabalho (se houver)",
                            "en":"Research plan (if available)"
                        },
                        "type":"File",
                    }),
                    Field({
                        "name":"supervisor-acceptance-letter",
                        "label":{
                            "pt":"Carta de anuência do orientador(a) (somente doutorado direto)",
                            "en":"Supervisor's letter of acceptance (only for Direct-entry PhD)",
                        },
                        "type":"File",
                    }),
                    Field({
                        "name": "masters-transcript",
                        "label": {
                            "pt": "Histórico escolar de mestrado, se houver",
                            "en": "Master's studies transcript, if applicable"
                        }, 
                        "type": "File",
                        "required": False, 
"description":{
    "pt":"Cópia digitalizada do seu histórico oficial de mestrado (se houver), com as disciplinas cursadas e as respectivas avaliações. ",
    "en":"Scanned copy of your official master's transcript (if any), including courses taken and the respective grades."
}
                    }),
                    Field({
                        "name": "masters-thesis-articles",
                        "label": {
                            "pt": "Dissertação de mestrado e/ou artigos científicos, se houverem",
                            "en": "Master's thesis and/or scientific articles, if available"
                        }, 
                        "type": "File",
                        "required": False, 
                        "description":{
                            "pt":"Cópia do texto de dissertação de mestrado e/ou de artigos científicos publicados ou no prelo, em formato PDF, quando existentes",
                            "en":"PDF copy of your master's thesis manuscript and/or published or in‑press scientific articles, when available."
                        }
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
                        "name": "usp_postgraduate_courses",
                        "label": {
                            "pt": "Disciplinas de Pós-Graduação na USP cursadas como aluno/a especial ou regular?",
                            "en": "Postgraduate courses at USP taken as a special or regular student?"
                        },
                        "description": {
                            "pt": '''
                            Para cada disciplina de pós-graduação cursada na USP, escreva a sigla da disciplina, o nome da disciplina,  o ano e a nota ou conceito, por exemplo, por exemplo,  MAC5711 Análise de Algoritmos, Conceito A. Não mencione disciplinas cursadas em outras instituições nem cursos de verão, disciplinas de graduação etc (você pode informar tais cursos na sua carta de motivação, em seu currículo ou no campo informações adicionais adiante).
''',
                            "en": '''
For each postgraduate course taken at USP, write the course code, course name, year and grade or concept (for example: MAC5711 Analysis of Algorithms, Grade A). Do not mention courses taken at other institutions, summer courses or undergraduate courses (you may report those in your motivation letter, CV or the additional information field).
'''
                        },
                        "type": "LongText"
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
If you are or were recently employed, describe your position, company and type of work. Leave blank if you have not had recent paid work or prefer not to share this information.

Example: Frontend Software Developer, SuperTec Soluções, since 2016 – developing software solutions for company clients.
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
                            Usaremos essa informação para recomendar um orientador caso você sua candidatura seja aceita no programa. Acesse https://www.ime.usp.br/pos-computacao/areas-pesquisa/ para conhecer os docentes separados por linhas de pesquisa; recomenda-se fortemente que você entre em conhecimento com o trabalho dos docentes antes de escolher uma área. Uma forma de fazer isso é olhar o nome e as publicações do docente no Google Scholar (scholar.google.com).
        ''',
                            "en": '''
We will use this information to recommend an advisor if your application is accepted. Visit https://www.ime.usp.br/pos-computacao/areas-pesquisa/ to see faculty grouped by research lines; it is strongly recommended that you familiarize yourself with faculty work before choosing an area. One way to do this is to check the faculty member's name and publications on Google Scholar (scholar.google.com).
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
                                    "pt": "Aprendizado de máquina e ciência de dados",
                                    "en": "Machine learning and data science."
                                }
                            }),
                            Options({
                                "value":{
                                    "pt":"Inteligência artificial e métodos formais",
                                    "en":"Artificial Intelligence and formal methods"
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
                                    "pt": "Métodos numéricos de otimização linear e não-linear.",
                                    "en": "Computational Methods for Linear and Non-linear Optimization."
                                }
                            }),
                            Options({ 
                                "value": {
                                    "pt": "Aprendizado de máquina e ciência de dados",
                                    "en": "Machine learning and data science."
                                }
                            }),
                            Options({
                                "value":{
                                    "pt":"Inteligência artificial e métodos formais",
                                    "en":"Artificial Intelligence and formal methods"
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
Texto conciso descrevendo os motivos da solicitação de ingresso no programa, experiências em pesquisa e atividades acadêmicas relevantes (por exemplo iniciação científica, estágio em laboratório de pesquisa, participação em atividades de extensão e publicações científicas, entre outras), perspectivas em relação ao programa e seus interesses de pesquisa, com menção a um tema de pesquisa afim a algum orientador(a) do programa. 
''',
                            "en": '''
A concise text describing your reasons for applying, research experience and relevant academic activities (e.g., undergraduate research, lab internships, extension activities, publications), your perspectives regarding the program and your research interests, mentioning a research topic related to a potential advisor in the program.
'''
                        },
                    }),
                                        Field({
                        "name": "scholarship",
                        "label": {
                            "pt": "Deseja concorrer a bolsa de estudos institucional (Capes ou CNPq)?",
                            "en": "Do you want to apply for an Institutional Scholarship?"
                        },
                        "required":True,
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
              Field({
                        "name":"name-contact-recommenders",
                        "label":{
                            "pt":"Nome e contato de dois recomendadores",
                            "en":"Name and contact of two recommenders"
                        },
                        "description":{
                            "pt":'''Forneça o endereço de e-mail ou telefone de dois recomendadores e breve descrição de seu relacionamento (p.ex. orientador de mestrado, IC ou TCC, ministrante de disciplina cursada, supervisor no trabalho). Essas pessoas poderão ser contatadas pela comissão de seleção.

Exemplo: Fulano da Silva, fulano@uni.br, ex-orientador de mestrado. Ciclana de Melo, ciclana@minhauni.br, professora em curso de pós-graduação e orientadora de iniciação científica.''',
                            "en":"Provide the email address or phone number of two recommenders and a brief description of your relationship with them (e.g., master's advisor, undergraduate research supervisor, course instructor, work supervisor). These persons may be contacted by the selection committee.\n\nExample: Fulano da Silva, fulano@uni.br, former master's advisor. Ciclana de Melo, ciclana@minhauni.br, professor in a graduate course and undergraduate research supervisor."
                        },
                        "required":True,
                        "type":"LongText",
                         
                    }),
              Field({
                  "name":"contacted-advisors",
                  "label":{
                      "pt":"Orientador(a) contatados",
                      "en":"Contacted advisors"
                  },
                  "description":{
                      "pt":'''Caso tenha entrado em contato com orientadores do programa (veja https://www.ime.usp.br/pos-computacao/orientadores/), descreva o tipo de contato realizado e coloque o nome da pessoa contatada. É altamente recomendável que seja feito um contato inicial antes de se candidatar ao programa.

Exemplo ruim: enviei e-mail para o Professor Fulaninho, mas ainda não obtive resposta.
Exemplo bom: conversei pessoalmente com a Professora Maria Amália sobre possível orientação e discutimos temas em potencial.''',
"en":"If you have contacted program advisors (see https://www.ime.usp.br/pos-computacao/orientadores/), describe the type of contact and the name of the person contacted. It is highly recommended to make an initial contact before applying.\n\nBad example: I sent an email to Professor Fulaninho but haven't received a reply yet.\nGood example: I spoke in person with Professor Maria Amália about possible supervision and we discussed potential research topics."
                  },
                  "required":False,
                  "type":"LongText"
              })
               ]
            }),
           Section({
                "title": {
                    "pt": "Informações adicionais",
                    "en": "Additional Information"
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