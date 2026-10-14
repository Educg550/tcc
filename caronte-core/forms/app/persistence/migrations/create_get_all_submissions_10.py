def run(db):
    with db.transaction() as f:
        f.sql('''
create or replace function get_all_submissions(
    p_form_id int,
    p_order_by int default 0,
    p_order_type int default 0,
    p_search text default '',
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
declare
    order_columns text[] := array['id', 'submitted_at', 'email'];
    order_directions text[] := array['desc', 'asc'];
    order_column text;
    order_direction text;
begin 
    if p_order_by < 0 or p_order_by >= array_length(order_columns, 1) then
        raise exception 'Invalid order_by index';
    end if;
    if p_order_type < 0 OR p_order_type >= array_length(order_directions, 1) then
        raise exception 'Invalid order_type index';
    end if;

    order_column := order_columns[p_order_by + 1];
    order_direction := order_directions[p_order_type + 1];

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
            and unaccent(r.value) ilike unaccent(%L)
        inner join form_field
            on r.field_id = form_field.id
        inner join form f
            on f.id = form_response.form_id
        where form_response.form_id = %s
            and form_response.submitted_at is not null  -- para nao pegar respostas em andamento
        group by form_response.id
        order by %I %s, form_response.id DESC
        $f$,
        p_lang,
        '%' || p_search || '%',
        p_form_id,
        order_column,
        order_direction
    );
end;
$$ LANGUAGE plpgsql;
        ''')