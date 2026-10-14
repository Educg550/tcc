def run(db):
    with db.transaction() as f:
        f.sql('''
create or replace function get_all_user_forms(
    p_user_id int default null,
    p_order_by int default 0,
    p_order_type int default 0,
    p_tag_filter jsonb default null,
    p_search text default '',
    p_lang text default 'pt',
    p_is_admin boolean default false
)
returns table(
    id int,
    title text,
    created_at timestamp,
    created_by text,
    tags jsonb,
    phase form_phase
)
language plpgsql
as $$
declare
    order_columns text[] := array['id', 'title', 'created_at'];
    order_directions text[] := array['desc', 'asc'];
    order_column text;
    order_direction text;
    condition text := '';
    key text;
    value text;
    user_filter text := '';
begin
    if p_user_id is not null then
        select role = 'administrator' into p_is_admin
        from users
        where users.id = p_user_id;
    end if;
              
    if p_order_by < 0 or p_order_by >= array_length(order_columns, 1) then
        raise exception 'Invalid order_by index';
    end if;
    if p_order_type < 0 OR p_order_type >= array_length(order_directions, 1) then
        raise exception 'Invalid order_type index';
    end if;

    order_column := order_columns[p_order_by + 1];
    order_direction := order_directions[p_order_type + 1];

    if p_tag_filter is not null then
        for key, value in select * from jsonb_each_text(p_tag_filter)
        loop
            if value is not null and value <> '' then
                condition := condition || format(' and form.tags ->> unaccent(%L) ilike unaccent(%L)', key, '%' || value || '%');
            end if;
        end loop;
    end if;
              
    user_filter := case when p_is_admin then '' else format(' and (form.created_by = %s or form_collaborators.user_id = %s)', p_user_id, p_user_id) end;

    return query execute format($q$
        select 
            form.id, 
            coalesce(form.title ->> %L, form.title ->> 'pt') as title,
            form.created_at,
            users.email as created_by,
            form.tags,
            form.phase
        from form
            left join users on form.created_by = users.id
            left join form_collaborators on form.id = form_collaborators.form_id
        where 
            unaccent(coalesce(form.title ->> %L, form.title ->> 'pt')) ilike unaccent(%L)
            %s
            %s
            order by %I %s
    $q$, p_lang, p_lang, '%' || p_search || '%', user_filter, condition, order_column, order_direction);
end;
$$;
        ''')