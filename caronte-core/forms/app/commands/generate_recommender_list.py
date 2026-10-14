from datetime import datetime
import os
import json

from app.entities.FormResponse import FormResponse
from app.exceptions.error_messages import ERROR
from app.extension import get_locale
from app.logger import Logger
from app.config import load_config

from app.common import to_csv, print_csv
from app.common.Result import Result
from app.services.form_service import get_all_submissions_dict, get_response_info, get_shared_token_info, update_metadata_submission
from app.services.response_service import create_partial_response
from app.services.section_service import get_fields_by_section, get_section_by_id
from app.services.token_service import create_shared_token, get_or_create_response_token

path_tmp = "tmp"

def run(db, application_form_id, recommender_form_id, expiration_at):
    Result(message=ERROR())

    config = load_config()

    tmp_recommender = []

    order_by = 1
    order_type = 0
    list_submissions = get_all_submissions_dict(db, int(application_form_id), order_by, order_type)
    for submission in list_submissions.data:
        metadata = submission["metadata"]
        if "send_to_recommender" in metadata and metadata["send_to_recommender"] is True:
            continue

        merged_dict = {}
        for d in submission["responses"]:
            merged_dict.update(d)

        application_name = merged_dict["fullname"]["value"]

        recommenders = [
            {
                "name_recommender": merged_dict["recommended-name-1"]["value"],
                "email_recommender": merged_dict["recommended-email-1"]["value"]
            },
            {
                "name_recommender": merged_dict["recommended-name-2"]["value"],
                "email_recommender": merged_dict["recommended-email-2"]["value"]
            }
        ]

        for recommender in recommenders:
            if not recommender["email_recommender"]:
                continue
            
            if not isinstance(expiration_at, datetime):
                expiration_at = datetime.strptime(expiration_at.split(" ")[0], "%Y-%m-%d")

            recommender_token = create_shared_token(db, {
                "form_id": int(recommender_form_id),
                "unique_answers": True,
                "expiration_at": expiration_at,
                "is_public": False,
            })

            token_data = get_shared_token_info(db, token=str(recommender_token))

            form_response = FormResponse({
                "email": recommender["email_recommender"],
                "metadata": { }
            })

            response_token = get_or_create_response_token(db, token_data.data, form_response)
            token_data = get_response_info(db, str(response_token.data["token"]))

            response_id = token_data.data['id']
            form_id = token_data.data['form_id']
            current = token_data.data['current_section']

            entry_list = {
                "fullname-candidate": application_name,
                "fullname": recommender["name_recommender"]
            }

            sections = get_section_by_id(db, int(recommender_form_id))
            current_section = sections.data[current]

            section = get_fields_by_section(db, form_id, current_section["id"], lang=get_locale())

            create_partial_response(db, response_id, section.data["fields"], entry_list, ignore_validations=False, entry=entry_list)
    
            url = f'{config["BASE_URL"]}/form/{str(response_token.data["token"])}'
            
            tmp_recommender.append({
                "response_id": submission["id"],
                "nome_candidato": application_name,
                "nome_recomendado": recommender["name_recommender"],
                "email_recomendado": recommender["email_recommender"], 
                "expiracao": expiration_at,
                "url": url
            })

        metadata["send_to_recommender"] = False
        update_metadata_submission(db, submission["id"], json.dumps(metadata))
        
    tmpcsvfile = to_csv(Result(data=tmp_recommender))
    print_csv(tmpcsvfile)
    file = f'{path_tmp}/tmp_recommenders.csv'
    Logger.print.info(f"Save in: {file}")
    os.makedirs(path_tmp, exist_ok=True)
    with open(file, mode='w') as f:
        f.write(tmpcsvfile.getvalue())

    return Result(file, f"Submetido e salvo em: {file}")

