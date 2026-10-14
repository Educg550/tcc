TABLE_NAME = 'field_option'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                field_id integer references form_field on delete cascade,
                value jsonb not null default '{{}}'::jsonb,
                metadata jsonb
            );
        ''')