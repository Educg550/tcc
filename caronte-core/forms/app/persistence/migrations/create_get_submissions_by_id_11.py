def run(db):
    with db.transaction() as f:
        f.sql('''
create or replace function get_submissions_by_id(
    p_response_id int,
    p_lang text default 'pt'
)
returns table(
    id int,
    token uuid,
    submitted_at timestamp,
    metadata jsonb,
    email text,
    responses jsonb
) as $$
begin
    return query execute format(
        $f$
        select
            form_response.id,
            form_response.token,
            form_response.submitted_at,
            form_response.metadata,
            form_response.email,
            json_agg(
                json_build_object(
                    form_field.name, json_build_object(
                        'label', coalesce(form_field.label ->> %L, form_field.label ->> 'pt'),
                        'value', r.value
                    )
                )
            )::jsonb as responses
        from form_response
        inner join responses r
            on form_response.id = r.response_id
        inner join form_field
            on r.field_id = form_field.id
        where 
            form_response.id = %s
            and form_response.submitted_at is not null  -- para nao pegar respostas em andamento
        group by form_response.id
        order by form_response.id DESC
        $f$,
        p_lang,
        p_response_id
    );
end;
$$ LANGUAGE plpgsql;
        ''')