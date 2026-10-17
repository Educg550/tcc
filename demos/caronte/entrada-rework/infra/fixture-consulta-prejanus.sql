-- Estado de consulta; aplicar depois de seed.sql e fixture-prejanus.sql, em banco sem inscrições.
-- Registro local da inscrição 1 do forms, que o original exige antes de listá-la (issue 26).
INSERT INTO submission (id, edict_id, candidate_form_id, recommenders_form_ids,
    stats, entry_semester, letter_sent, candidate_form_version,
    recommender_form_version, created_at)
VALUES (1, 1, 1, '[]', 'underreview', 'Primeiro semestre.', false, 1, 1,
    TIMESTAMPTZ '2026-10-16 12:00:00+00');

SELECT setval(pg_get_serial_sequence('submission', 'id'), (SELECT max(id) FROM submission));
