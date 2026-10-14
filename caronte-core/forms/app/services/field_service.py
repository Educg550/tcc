import json
from app.common.Result import Result

from app.exceptions.error_messages import INVALID_FIELDS

def get_fields(db, form_id) -> Result:
    if form_id is None: 
        return Result([])

    sql_string = '''
        select form_field.* from form_field
        inner join form_section
            on form_field.section_id = form_section.id
        where form_field.form_id = %s and form_section.is_active = true
        order by form_field.position;
    '''

    fields = None
    with db.transaction() as f:
        fields = f.sql_dict(sql_string, (form_id,), callback=lambda x : x.fetchall())

    if not fields: 
        return Result([])

    return Result(fields)

def get_field_by_name(db, form_id, name) -> Result:
    if form_id is None or name is None: 
        return Result()

    sql_string = '''
        select form_field.* from form_field
        inner join form_section
            on form_field.section_id = form_section.id
        where form_field.form_id = %s
            and form_field.name = %s
            and form_section.is_active = true;
    '''

    field = None
    with db.transaction() as f:
        field = f.sql_dict(sql_string, (form_id, name,), callback=lambda x : x.fetchone())

    if field is None: 
        return Result(message=INVALID_FIELDS(name))

    return Result(dict(field))

def update_field_by_id(db, field_id, field_data):
    if field_id is None: 
        return Result()
    
    sql_string = '''
        update form_field
            set label = %s, description = %s
            where id = %s
    '''

    with db.transaction() as f:
        f.sql_dict(sql_string, (json.dumps(field_data["label"]), json.dumps(field_data["description"]), field_id,))

    return Result(True)

def get_field_by_position(db, form_id, position) -> Result:
    if form_id is None or position is None: 
        return Result()

    sql_string = '''
        select * from form_field
            where form_id = %s
            and position = %s
    '''

    field = None
    with db.transaction() as f:
        field = f.sql_dict(sql_string, (form_id, position,), callback=lambda x : x.fetchone())

    if field is None: 
        return Result(message=INVALID_FIELDS())

    return Result(dict(field))
    