def run(db):
    with db.transaction() as f:
        f.sql('''
            create or replace function update_form_response_section(
                p_id int,
                p_current_section int
            )
            returns table(id int, current_section int)
            language plpgsql
            security definer
            set search_path = public
            as $$
            begin
                return query
                update form_response
                    set current_section = p_current_section
                where form_response.id = p_id
                returning form_response.id, form_response.current_section;
            end;
            $$;
        ''')