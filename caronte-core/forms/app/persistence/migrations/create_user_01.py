TABLE_NAME = 'users'

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            create table if not exists {TABLE_NAME} (
                id serial primary key,
                email text not null unique,
                created_at timestamp,
                role text default 'common'
            );
        ''')