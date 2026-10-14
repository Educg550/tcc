import json
import re
from app.common.Result import Result
from app.common.validators import is_required_filled, is_valid_regex
from app.entities.FormResponse import FormResponseType
from app.entities.Response import Response
from app.exceptions.error_messages import ERROR_REQUIRED_FIELDS, ERROR_SUBMIT_FORM, INVALID_FIELDS, SUBMIT_FORM

from app.repositories.response_repository import insert_form_response, insert_or_update_response
from app.services.field_service import get_fields
from app.services.token_service import get_shared_token_info

def parse_checkbox_field(field, responses):
    datas = {}
    pattern = re.compile(rf"^{re.escape(field['name'])}\[(\d+)\]$")
    for key, value in responses.items():
        match = pattern.match(key)
        if field["name"] in key and match:
            index = int(match.group(1)) - 1
            datas[index] = value
    arr = []
    if datas:
        max_index = max(datas.keys())
        arr = [""] * (max_index + 1)
        for i, valor in datas.items():
            arr[i] = valor
    else:
        arr = []

    return arr

def build_response_objects(fields, responses, entry, ignore_validations = False) -> Result:
    result_data = {}

    for field in fields:
        name = field["name"]

        if name in entry:
            result_data[name] = entry[name]

        if field.get("disabled", False):
            continue

        if field["type"] == "CheckBox":
            parsed_checkbox = parse_checkbox_field(field, responses)
            result_data[name] = json.dumps(parsed_checkbox)
            
            if not ignore_validations:
                if field.get("required") and len(parsed_checkbox) <= 0:
                    return Result(message=ERROR_REQUIRED_FIELDS(field["label"]))
        else:
            if name in responses:
                result_data[name] = responses[name]

            if not ignore_validations:
                if not is_required_filled(field, responses):
                    return Result(message=ERROR_REQUIRED_FIELDS(field["label"]))
                
                if name in responses and responses[name] and not is_valid_regex(field, responses[name]):
                    return Result(message=INVALID_FIELDS(field["label"]))
        
    response_list = [ Response({'name': k, 'value': v.strip()}) for k, v in result_data.items() ]
    
    field_map = { field["name"]: field["id"] for field in fields }
    for response in response_list:
        if response["name"] in field_map:
            response["field_id"] = field_map[response["name"]]

    return Result(response_list)

def create_partial_upload(db, response_id, partial_fields, responses, ignore_validations, entry={}):
    result = build_response_objects(partial_fields, responses, entry, ignore_validations)
    if not result.succeeded:
        return result

    with db.transaction() as f:
        for response in result.data:
            insert_or_update_response(f, response_id, response)
    
    return Result(True, message=SUBMIT_FORM())

def create_partial_response(db, response_id, partial_fields, responses, ignore_validations, entry={}):
    result = build_response_objects(partial_fields, responses, entry, ignore_validations)
    if not result.succeeded:
        return result

    with db.transaction() as f:
        for response in result.data:
            insert_or_update_response(f, response_id, response)
    
    return Result(True, message=SUBMIT_FORM())

def create_response(db, form_response: FormResponseType, responses, entry={}) -> Result:
    if "token" in form_response.keys():
        res = get_shared_token_info(db, token=form_response["token"].strip())
        if not res.succeeded: 
            return res

        form_response["shared_id"] = res.data["shared_id"]
        form_response["form_id"] = res.data["form_id"]
        form_response["form_version"] = res.data.get("version", 1)

    if "form_id" not in form_response.keys(): 
        return Result()

    fields = get_fields(db, form_response["form_id"])
    
    response_list = build_response_objects(fields, responses, entry)
    if not response_list.succeeded:
        return response_list
    form_response["responses"] = response_list.data

    result = Result(message=ERROR_SUBMIT_FORM())
    with db.transaction() as f:
        form_response_info = insert_form_response(f, form_response)

        if "responses" not in form_response.keys():
            return Result(form_response_info["id"])

        for response in form_response["responses"]:
            insert_or_update_response(f, form_response_info["id"], response)

        return Result(form_response_info["id"], message=SUBMIT_FORM())
    return result

def finalize_response(db, response_id):
    sql_string = '''
    update form_response
        set submitted_at = now()
        where id = %s
    returning id;
    '''

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (response_id,), callback=lambda x : x.fetchone())

    return Result(res)

def get_partial_response(db, response_id, field_ids) -> Result:
    sql_string = '''
        select responses.field_id, responses.value, form_field.position, form_field.type
            from responses
        inner join form_field 
            on form_field.id = responses.field_id
        where response_id = %s
            and responses.field_id = any(%s)
    '''

    field = None
    with db.transaction() as f:
        field = f.sql_dict(sql_string, (response_id, field_ids,), callback=lambda x : x.fetchall())

    return Result(field)

def get_response_info(db, token_str) -> Result:
    sql_string = '''
        select 
            form_response.id, form_response.form_id, form_response.current_section, form_response.shared_id, form_response.email, form_response.submitted_at, form.phase
        from form_response
            inner join form on form.id = form_response.form_id
            where form_response.token = %s;
    '''

    token = None
    with db.transaction() as f:
        token = f.sql_dict(sql_string, (token_str,), callback=lambda x : x.fetchone())

    return Result(token)