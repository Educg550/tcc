import csv
import os
import json
import locale
from datetime import datetime

from app.common.Result import Result
from app.logger import Logger
from app.config import load_config

from app.services.email_service import Email
from app.services.form_service import get_submissions_by_id, update_metadata_submission

def template_email(name_recommender, name_application, notice, url, expiration_at):
    return {"html": f"""\
<p>Prezado(a) {name_recommender}<sup>[1]</sup>,</p>

<p>Você foi indicado(a) para escrever uma carta de recomendação de "{name_application}", que está participando do processo seletivo para o programa de Pós-Graduação em Ciência da Computação do Instituto de Matemática e Estatística da Universidade de São Paulo.</p>

<p>Pedimos, por favor, que preencha o formulário de recomendação no link abaixo:</p>

<a href="{url}">Link para o formulário de recomendação</a> (Envio Único)

<p>Todas as informações fornecidas no formulário são sigilosas para o/a candidato/a.</p>

<p>Pedimos, por gentileza, que o formulário seja preenchido em até 10 dias após o recebimento deste e-mail.</p>

<p>Caso não reconheça a origem desta mensagem, por gentileza, desconsidere o conteúdo.</p>

<br/>

<p><sup>[1]</sup> Todas as informações pessoais, como nomes e e-mails, foram fornecidas por "{name_application}".</p>
"""}

def run(db, file):
    config = load_config()
    email = Email(config)

    reader = csv.DictReader(file, delimiter=',')
    for row_reader in reader:
        response_id = row_reader["response_id"]

        submission = get_submissions_by_id(db, response_id)
        if not submission.succeeded:
            continue

        name_recommender = row_reader["nome_recomendado"]
        notice = "Mestrado" # TODO: programa de mestrado ou pos doutorado
        name_application = row_reader["nome_candidato"]
        email_recommender = row_reader["email_recomendado"]
        expiration_at = datetime.strptime(row_reader["expiracao"].split(" ")[0], "%Y-%m-%d")
        url = row_reader["url"]

        locale.setlocale(locale.LC_ALL, '')
        email_result = email.send_queue({
            "to_addrs": [email_recommender], 
            "subject": "Solicitação de recomendação para candidatura", 
            "body": template_email(name_recommender, name_application, notice, url, expiration_at)
        })
        
        assert email_result.succeeded, email_result.message

        Logger.print.info(f"Email sent successfully to {email_recommender}.")

        metadata = submission.data["metadata"]
        metadata["send_to_recommender"] = True
        update_metadata_submission(db, submission.data["id"], json.dumps(metadata))

    os.remove(file.name)
    file.close()
    return Result(file, "Submetido e salvo em: {file}")
