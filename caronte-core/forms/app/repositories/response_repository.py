from app.common import get_values
from app.entities.FormResponse import FormResponse

def insert_form_response(f, form_response):
    insert = get_values(FormResponse, form_response)

    sql_string = f'''
        insert into form_response({",".join(insert.keys())}) 
            values({",".join(["%s" for _ in range(len(insert))])}) returning id, current_section;   
    '''

    return f.sql_dict(sql_string, tuple(insert.values()), callback=lambda x : x.fetchone())

def insert_or_update_response(f, response_id, response) -> bool:
    sql_string = '''
        insert into responses(response_id, field_id, value) 
            values(%s, %s, %s) 
        on conflict (response_id, field_id)
        do update set value = excluded.value    
        returning id
    '''

    f.sql_dict(sql_string, (response_id, response["field_id"], response["value"],), callback=lambda x : x.fetchone())