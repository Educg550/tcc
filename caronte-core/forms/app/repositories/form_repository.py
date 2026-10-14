def get_form_dict_raw(db, form_id, lang):
    sql_string = """
        select
            coalesce(form.title ->> %s, form.title ->> 'pt') as title,
            coalesce(form.description ->> %s, form.description ->> 'pt') as description,

            form.created_at,
            form.created_by,
            form.tags,
            form.metadata,

            json_agg(
                json_build_object(
                    'name', form_field.name,
                    'label', coalesce(form_field.label ->> %s, form_field.label ->> 'pt'),
                    'type', form_field.type,
                    'placeholder', form_field.placeholder,
                    'required', form_field.required,
                    'disabled', form_field.disabled,
                    'validation', form_field.validation,
                    'prefix', form_field.prefix,
                    'error_message', coalesce(form_field.error_message ->> %s, form_field.error_message ->> 'pt'),
                    'position', form_field.position,
                    'description', coalesce(form_field.description ->> %s, form_field.description ->> 'pt'),
                    'options', (
                        select 
                            array_agg(
                                coalesce(field_option.value ->> %s, field_option.value ->> 'pt')
                            ) 
                        from field_option
                        where field_option.field_id = form_field.id             -- similar left join
                    )
                ) order by form_field.position
            ) as fields
        from form
            inner join form_section
            on form.id = form_section.form_id and form_section.is_active = true
            inner join form_field
            on form_section.id = form_field.section_id
        where
            form.id = %s
        group by form.id, form.title, form.description, form.metadata;
    """
    with db.transaction() as f:
        return f.sql_dict(
            sql_string,
            (
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                form_id,
            ),
            callback=lambda x: x.fetchone(),
        )


def get_viewer_form_dict_raw(db, form_id, lang):
    sql_string = """
        select
            coalesce(form.title ->> %s, form.title ->> 'pt') as title,
            coalesce(form.description ->> %s, form.description ->> 'pt') as description,
            form.created_at,
            form.created_by,
            form.tags,
            form.metadata,

            json_agg(
                json_build_object(
                    'id', form_section.id,
                    'title', coalesce(
                        form_section.title ->> %s,
                        form_section.title ->> 'pt'
                    ),
                    'description', coalesce(
                        form_section.description ->> %s,
                        form_section.description ->> 'pt'
                    ),
                    'position', form_section.position,

                    'fields', (
                        select json_agg(
                            json_build_object(
                                'id', form_field.id,
                                'name', form_field.name,
                                'label', coalesce(
                                    form_field.label ->> %s,
                                    form_field.label ->> 'pt'
                                ),
                                'type', form_field.type,
                                'placeholder', form_field.placeholder,
                                'required', form_field.required,
                                'disabled', form_field.disabled,
                                'validation', form_field.validation,
                                'prefix', form_field.prefix,
                                'error_message', coalesce(
                                    form_field.error_message ->> %s,
                                    form_field.error_message ->> 'pt'
                                ),
                                'position', form_field.position,
                                'description', coalesce(
                                    form_field.description ->> %s,
                                    form_field.description ->> 'pt'
                                ),
                                'options', (
                                    select array_agg(
                                        coalesce(
                                            field_option.value ->> %s,
                                            field_option.value ->> 'pt'
                                        )
                                    )
                                    from field_option
                                    where field_option.field_id = form_field.id
                                )
                            )
                            order by form_field.position
                        )
                        from form_field
                        where form_field.section_id = form_section.id
                    )
                )
                order by form_section.position
            ) as sections

        from form
        inner join form_section
            on form.id = form_section.form_id
            and form_section.is_active = true

        where form.id = %s

        group by
            form.id,
            form.title,
            form.description,
            form.metadata;
    """

    with db.transaction() as f:
        return f.sql_dict(
            sql_string,
            (
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                form_id,
            ),
            callback=lambda x: x.fetchone(),
        )


def get_partial_form_dict_raw(db, form_id, section_id, lang="pt"):
    if section_id is None:
        return []

    sql_string = """
        select
            coalesce(form.title ->> %s, form.title ->> 'pt') as title,
            coalesce(form.description ->> %s, form.description ->> 'pt') as description,

            coalesce(form_section.title ->> %s, form_section.title ->> 'pt') as title_section,
            coalesce(form_section.description ->> %s, form_section.description ->> 'pt') as description_section,
            
            json_agg(
                json_build_object(
                    'id', form_field.id,
                    'name', form_field.name,
                    'label', coalesce(form_field.label ->> %s, form_field.label ->> 'pt'),
                    'type', form_field.type,
                    'placeholder', form_field.placeholder,
                    'required', form_field.required,
                    'disabled', form_field.disabled,
                    'validation', form_field.validation,
                    'prefix', form_field.prefix,
                    'error_message', coalesce(form_field.error_message ->> %s, form_field.error_message ->> 'pt'),
                    'position', form_field.position,
                    'description', coalesce(form_field.description ->> %s, form_field.description ->> 'pt'),
                    'options', (
                        select 
                            array_agg(
                                coalesce(field_option.value ->> %s, field_option.value ->> 'pt')
                            ) as options
                        from field_option
                        where field_option.field_id = form_field.id             -- similar left join
                    )
                ) order by form_field.position
            ) as fields
        from form
            inner join form_section
                on form.id = form_section.form_id and form_section.is_active = true
            inner join form_field
                on form_section.id = form_field.section_id
        where
            form.id = %s and form_section.id = %s
        group by form.id, form_section.id;
    """

    with db.transaction() as f:
        return f.sql_dict(
            sql_string,
            (
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                lang,
                form_id,
                section_id,
            ),
            callback=lambda x: x.fetchone(),
        )
