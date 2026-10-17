INSERT INTO "user" (id, email, name, nusp, role) VALUES
    (1, 'dev@example.com', 'Dev User', '0000000', 'administrator'),
    (2, 'docente@example.com', 'Docente', '0000001', 'teacher')
ON CONFLICT (id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('"user"', 'id'), (SELECT max(id) FROM "user"));
