TABLE_NAME = 'form_shared'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                form_id integer references form on delete cascade,
                unique_answers boolean default false,
                is_public boolean default false,
                token uuid not null unique,
                created_at timestamp,
                expiration_at timestamp
            );
        ''')