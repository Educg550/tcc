TABLE_NAME = 'responses'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                response_id integer references form_response on delete cascade,
                field_id integer references form_field on delete set null,
                value text,
                unique(response_id, field_id)
            );
        ''')