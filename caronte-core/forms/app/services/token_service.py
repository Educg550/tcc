from datetime import datetime, timedelta, date
import uuid
from app.common import get_values
from app.common.Result import Result
from app.entities.Token import Token, TokenType
from app.exceptions.error_messages import ERROR_TOKEN, TOKEN_UNAVAILABLE
from flask_babel import gettext
from app.repositories.response_repository import insert_form_response

EXPIRATION_TIME = 7#days

def get_shared_token_info(db, token="", shared_id=None) -> Result:
    __shared_id = None
    __form_id = None
    __unique_answers = None
    __expiration_at = None

    if shared_id is None:
        # check if exist token
        sql_string = '''
            select form_shared.id, form_shared.form_id, form_shared.unique_answers, form_shared.is_public, form_shared.expiration_at, form.phase, form.version from form_shared
                inner join form on form.id = form_shared.form_id
                where form_shared.token = %s;
        '''

        res = None
        with db.transaction() as f:
            res = f.sql_dict(sql_string, (token,), callback=lambda x : x.fetchone())

        if res is None: 
            return Result(message=ERROR_TOKEN())
        
        today = date.today()
        if res["phase"] == "Registration" and res["expiration_at"].date() < today:
            return Result(message=TOKEN_UNAVAILABLE())

        if res["phase"] == "Completed":
            return Result(message=TOKEN_UNAVAILABLE())

        __shared_id = res["id"]
        __form_id = res["form_id"]
        __unique_answers = res["unique_answers"]
        __expiration_at = res["expiration_at"]
        __phase = res["phase"]
        __version = res.get("version") or 1
    else:
        sql_string = '''
            select form_shared.id, form_shared.form_id, form_shared.unique_answers, form_shared.is_public, form_shared.expiration_at, form.phase, form.version from form_shared
                inner join form on form.id = form_shared.form_id
                where form_shared.id = %s;
        '''

        res = None
        with db.transaction() as f:
            res = f.sql_dict(sql_string, (shared_id,), callback=lambda x : x.fetchone())

        if res is None: 
            return Result(message=ERROR_TOKEN())   

        today = date.today()
        if res["phase"] == "Registration" and res["expiration_at"].date() < today:
            return Result(message=TOKEN_UNAVAILABLE())
        
        if res["phase"] == "Completed":
            return Result(message=TOKEN_UNAVAILABLE())
        
        __shared_id = shared_id
        __expiration_at = res["expiration_at"]
        __unique_answers = res["unique_answers"]
        __phase = res["phase"]
        __version = res.get("version") or 1

    return Result({ "shared_id": __shared_id, "form_id": __form_id, "unique_answers": __unique_answers, "expiration_at": __expiration_at, "phase": __phase, "version": __version })

def get_or_create_response_token(db, shared, form_response):
    phase = shared.get("phase")

    if phase == 'Completed':
        return Result(message=gettext("Este formulário está fechado para envios e edições."))
    
    if phase == 'Approval':
        return Result(message=gettext("Este formulário está fechado para envios e edições, apenas é possível caso solicitado pelo administrador."))
    
    if shared.get("unique_answers"):
        sql_string = '''
            select 
                form_response.id, form_response.token, form_response.current_section
            from form_response
            where 
                form_response.shared_id = %s and
                form_response.email = %s
        '''

        with db.transaction() as f:
            res = f.sql_dict(sql_string, (shared["shared_id"], form_response["email"], ), callback=lambda x : x.fetchone())
        if res is not None:
            # define section equal 0
            from app.services.section_service import set_section
            section = set_section(db, res["id"], 0)
            
            if not section.succeeded:
                return Result(message=gettext("Ocorreu uma falha ao criar o formulário."))
                
            return Result({ "token": res['token'], "current_section":  section.data["current_section"] })

    new_token = uuid.uuid4()
    response_token = str(new_token)

    form_response["form_id"] = shared["form_id"]
    form_response["shared_id"] = shared["shared_id"]
    form_response["token"] = response_token
    form_response["form_version"] = shared.get("version") or 1

    response = None
    with db.transaction() as f:
        response = insert_form_response(f, form_response)

    return Result({ "token": response_token, "current_section":  response["current_section"] })

def get_all_tokens_by_form_id(db, form_id):
    "**admin command**"
    sql_string = '''
        select id, unique_answers, token, created_at, expiration_at, is_public from form_shared
        where
            form_shared.form_id = %s;
    '''

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (form_id, ), callback=lambda x : x.fetchall())

    return Result(res)

def get_token_by_id(db, token_id):
    sql_string = '''
        select expiration_at, unique_answers, is_public from form_shared
        where id = %s;
    '''

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (token_id, ), callback=lambda x : x.fetchone())

    return Result(res)

def create_shared_token(db, shared_token_response: TokenType):
    "**admin command**"
    new_token = uuid.uuid4()
    shared_token_response["token"] = str(new_token)
    shared_token_response["created_at"] = datetime.today()
    if "expiration_at" not in shared_token_response:
        shared_token_response["expiration_at"] = datetime.today() + timedelta(days=EXPIRATION_TIME)
    else:
        shared_token_response["expiration_at"] = shared_token_response["expiration_at"]

    insert = get_values(Token, shared_token_response)

    sql_string = f'''
        insert into form_shared({",".join(insert.keys())}) 
            values({",".join(["%s" for _ in range(len(insert))])}) returning id;   
    '''

    with db.transaction() as f:
        f.sql(sql_string, tuple(insert.values()), callback=lambda x : x.fetchone())[0]

    return new_token

def edit_shared_token(db, id, shared_token_response: TokenType):
    """
        **admin command**

        necessario chaves de shared_token_response serem controlados pelo servidor
    """

    if "unique_answers" not in shared_token_response:
        shared_token_response["unique_answers"] = False

    insert = get_values(Token, shared_token_response)

    sql_string = f'''
        update form_shared
            set {",".join([f"{key} = %s" for key in insert.keys()])} 
        where id = %s
        returning id;   
    '''

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (*insert.values(), id,), callback=lambda x : x.fetchone())

    return Result(res)