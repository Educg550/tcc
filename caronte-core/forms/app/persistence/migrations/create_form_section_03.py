TABLE_NAME = 'form_section'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                form_id integer references form on delete cascade,
                title jsonb not null default '{{}}'::jsonb,
                description jsonb not null default '{{}}'::jsonb,
                position integer default 0
            );
        ''')