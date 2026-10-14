def run(db):
    with db.transaction() as f:
        f.sql('''
            create or replace function change_form_phase(
                p_id int,
                p_phase form_phase
            )
            returns table(id int, phase form_phase)
            language plpgsql
            security definer
            set search_path = public
            as $$
            begin
                return query
                update form
                    set phase = p_phase
                where form.id = p_id
                returning form.id, form.phase;
            end;
            $$;
        ''')