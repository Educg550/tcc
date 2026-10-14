from . import TABLE_NAME_FORM

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            ALTER TABLE {TABLE_NAME_FORM}
            ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
        ''')
