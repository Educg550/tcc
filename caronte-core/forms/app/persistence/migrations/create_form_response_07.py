TABLE_NAME = 'form_response'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                form_id integer references form on delete cascade,
                shared_id integer references form_shared on delete set null,
                user_id integer references users on delete set null,
                email text,
                token uuid not null unique, -- token individual da resposta
                current_section integer default 0,
                submitted_at timestamp,
                metadata jsonb not null default '{{}}'::jsonb
            );
        ''')