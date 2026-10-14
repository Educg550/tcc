
TABLE_NAME = 'form_field'

def run(db):
    with db.transaction() as f:
        f.sql('''
            do $$
            begin
                if not exists (
                    select 1 from pg_type where typname = 'field_type'
                ) then
                    create type field_type as enum (
                        'Text',
                        'LongText',
                        'Number',
                        'CheckBox',
                        'Radio',
                        'Date',
                        'File'
                    );
                end if;
            end
            $$ language plpgsql;
        ''')

        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                form_id integer references form on delete cascade,
                section_id integer references form_section on delete set null,
                label jsonb not null default '{{}}'::jsonb,
                name text not null,
                description jsonb not null default '{{}}'::jsonb,
                type field_type not null,
                placeholder text,
                required boolean default false,
                disabled boolean default false,
                validation text,
                error_message jsonb not null default '{{}}'::jsonb,
                prefix text,
                position integer default 0
            );

            do $$
            begin
                if not exists (
                    select 1 from pg_constraint where conname = 'unique_form_name'
                ) then
                    alter table {TABLE_NAME}
                    add constraint unique_form_name unique (form_id, name);
                end if;
            end
            $$ language plpgsql;
        ''')
