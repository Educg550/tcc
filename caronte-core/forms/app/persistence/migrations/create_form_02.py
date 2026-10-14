TABLE_NAME = 'form'

def run(db):
    with db.transaction() as f:
        f.sql('''
            do $$
            begin
                if not exists (
                    select 1 from pg_type where typname = 'form_phase'
                ) then
                    create type form_phase as enum (
                        'Registration',
                        'Approval',
                        'Completed'
                    );
                end if;
            end
            $$ language plpgsql;
        ''')

        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                title jsonb not null default '{{}}'::jsonb,
                description jsonb not null default '{{}}'::jsonb,
                created_at timestamp,
                phase form_phase not null default 'Registration'::form_phase,
                created_by integer references users,
                tags jsonb not null default '{{}}'::jsonb,
                metadata jsonb not null default '{{}}'::jsonb
            );
        ''')