-- Estado de consulta; aplicar depois de fixture-forms.sql, em banco sem respostas.
-- Uma inscrição finalizada no formulário 1, com os 42 campos preenchidos nos formatos que o forms grava.
INSERT INTO form_response (id, form_id, shared_id, user_id, email, token,
    current_section, submitted_at, metadata, form_version)
VALUES (1, 1, 1, NULL, 'candidata.piloto@example.com',
    'c0a5e1f0-0000-4000-8000-000000000001', 7,
    TIMESTAMP '2026-10-16 12:00:00', '{}', 1);

INSERT INTO responses (response_id, field_id, value)
SELECT 1, f.id, v.value
FROM (VALUES
    ('acknowledgment', '["Estou ciente."]'),
    ('fullname', 'Ana Piloto Caronte'),
    ('mother-fullname', 'Maria Piloto Caronte'),
    ('birth', '1998-03-14'),
    ('biological-sex', 'Feminino'),
    ('nationality', 'Brasileira'),
    ('cpf', '123.456.789-09'),
    ('type-official-document', 'Carteira de Identidade Nacional (CIN)'),
    ('document-number', '12.345.678-9'),
    ('official-document-file', '00000000000000000000000000000001_official-document-file.pdf'),
    ('nusp', '12345678'),
    ('phone-number', '+55 11 99999-0001'),
    ('address', 'Rua do Matão, 1010, São Paulo - SP'),
    ('website', 'https://example.com/ana'),
    ('disabilities', '["Declaro que me identifico como PCD."]'),
    ('disabilities-file', '00000000000000000000000000000002_disabilities-file.pdf'),
    ('ethnicity-race', '["Declaro que me identifico como PPI."]'),
    ('ethnicity-race-file', '00000000000000000000000000000003_ethnicity-race-file.pdf'),
    ('lattes-cv', '1234567890123456'),
    ('lattes-cv-file', '00000000000000000000000000000004_lattes-cv-file.pdf'),
    ('course-of-graduation', 'Ciência da Computação'),
    ('year-of-graduation', '2021'),
    ('institution', 'Universidade Presbiteriana Mackenzie (Mackenzie)'),
    ('country-undergraduate', 'Brasil'),
    ('studies-transcripts', '00000000000000000000000000000005_studies-transcripts.pdf'),
    ('year-poscomp', '2025'),
    ('grades-poscomp', ''),
    ('poscomp-file', '00000000000000000000000000000006_poscomp-file.pdf'),
    ('graduate-courses-file', '00000000000000000000000000000007_graduate-courses-file.pdf'),
    ('current-job', 'Desenvolvedora de software em tempo parcial.'),
    ('primary-area', 'Engenharia de software e bancos de dados.'),
    ('secondary-area', 'Inteligência artificial e métodos formais.'),
    ('motivation-letter', '00000000000000000000000000000008_motivation-letter.pdf'),
    ('recommended-name-1', 'Paula Recomendadora Um'),
    ('recommended-email-1', 'recomendadora.um@example.com'),
    ('recommended-name-2', 'Pedro Recomendador Dois'),
    ('recommended-email-2', 'recomendador.dois@example.com'),
    ('semester', 'Primeiro semestre.'),
    ('intended-level', 'Integral e exclusiva (não vou desempenhar outras atividades).'),
    ('scholarship', 'Sim'),
    ('relevant-information', 'Informação adicional da fixture de consulta.'),
    ('about-this-program', 'Site do IME-USP')
) AS v(name, value)
JOIN form_field f ON f.form_id = 1 AND f.name = v.name AND f.is_active;

SELECT setval(pg_get_serial_sequence('form_response', 'id'), (SELECT max(id) FROM form_response));
SELECT setval(pg_get_serial_sequence('responses', 'id'), (SELECT max(id) FROM responses));
