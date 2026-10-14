TABLE_NAME = 'form_collaborators'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                form_id integer references form on delete cascade,
                user_id integer references users on delete set null,
                can_edit boolean default true,
                invited_by integer references users on delete set null,
                invited_at timestamp default now()
            );

            do $$
            begin
                if not exists (
                    select 1 from pg_constraint where conname = 'form_user_unique'
                ) then
                    alter table {TABLE_NAME}
                    add constraint form_user_unique unique (form_id, user_id);
                end if;
            end
            $$ language plpgsql;
        ''')