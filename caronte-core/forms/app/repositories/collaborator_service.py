def get_all_collaborator_by_form(db, form_id: int):
    sql_string = '''
        select 
            form_collaborators.form_id,
            form_collaborators.user_id,
            u_collab.email AS user_email,
            form_collaborators.can_edit,
            form_collaborators.invited_by,
            u_inviter.email AS invited_by_email,
            form_collaborators.invited_at
        from form_collaborators
        inner join users u_collab
            on u_collab.id = form_collaborators.user_id
        left join users u_inviter
            on u_inviter.id = form_collaborators.invited_by
        where form_collaborators.form_id = %s;
    '''

    with db.transaction() as f:
        return f.sql_dict(sql_string, (form_id,), callback=lambda x : x.fetchall())

def get_collaborator(
        db,
        form_id: int, 
        user_id: int
    ):
    sql_string = '''
        select 
            form_id,
            user_id,
            can_edit,
            invited_by,
            invited_at
        from form_collaborators
        where
            form_id = %s and
            user_id = %s
    '''

    with db.transaction() as f:
        return f.sql_dict(sql_string, (form_id, user_id,), callback=lambda x : x.fetchone())

def add_collaborator(db, form_id, invitee_id, can_edit, inviter_id):
    sql_string = '''
        insert into form_collaborators (form_id, user_id, can_edit, invited_by)
        values (%s, %s, %s, %s)
        on conflict (form_id, user_id) 
        do update set 
            can_edit = EXCLUDED.can_edit,
            invited_by = EXCLUDED.invited_by;
    '''

    with db.transaction() as f:
        f.sql_dict(sql_string, (form_id, invitee_id, can_edit, inviter_id))