from . import TABLE_NAME_FORM_SECTION, TABLE_NAME_FORM_FIELD, TABLE_NAME_FORM_RESPONSE

def run(db):
    with db.transaction() as f:
        f.sql(f'''
            ALTER TABLE {TABLE_NAME_FORM_SECTION}
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
            ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

            ALTER TABLE {TABLE_NAME_FORM_FIELD}
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
            ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

            ALTER TABLE {TABLE_NAME_FORM_RESPONSE}
            ADD COLUMN IF NOT EXISTS form_version INTEGER NOT NULL DEFAULT 1;

            ALTER TABLE {TABLE_NAME_FORM_FIELD}
            DROP CONSTRAINT IF EXISTS unique_form_name;

            CREATE UNIQUE INDEX IF NOT EXISTS unique_form_name_active
            ON {TABLE_NAME_FORM_FIELD} (form_id, name)
            WHERE is_active = true;
        ''')
