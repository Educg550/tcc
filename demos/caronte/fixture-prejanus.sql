-- Estado inicial do piloto; aplicar apenas em banco migrado e sem editais.
-- Usuários 1 e 2 vêm de seed.sql. Formulários e campos vêm de fixture-forms.sql.
-- Não cria candidaturas, recomendações preenchidas ou arquivos enviados.
INSERT INTO edict (id, title, description, candidate_forms, recommenders_forms,
    closed_date, year, semester, type, phase, is_open, user_id, created_at)
VALUES (1, 'Piloto TCC - Mestrado 2026', 'Fixture do piloto Caronte', '1', '2',
    DATE '2030-04-01', 2026, 1, 'mestrado', 'inscricoes', true, 1,
    TIMESTAMPTZ '2026-10-16 00:00:00+00');

INSERT INTO edict_phase (id, edict_id, phase, closed_date) VALUES
    (1, 1, 'inscricoes', DATE '2030-01-01'),
    (2, 1, 'homologacao', DATE '2030-02-01'),
    (3, 1, 'avaliacao', DATE '2030-03-01'),
    (4, 1, 'encerrado', DATE '2030-04-01');

INSERT INTO edict_form_mappings (id, edict_id, form_id, form_type, form_version,
    mapping, user_id, is_active, created_at) VALUES
    (1, 1, '1', 'candidate', 1,
    $mapping${
  "acknowledgment": {
    "section": 1,
    "field": 1
  },
  "fullname": {
    "section": 2,
    "field": 2
  },
  "mother-fullname": {
    "section": 2,
    "field": 3
  },
  "birth": {
    "section": 2,
    "field": 4
  },
  "biological-sex": {
    "section": 2,
    "field": 5
  },
  "nationality": {
    "section": 2,
    "field": 6
  },
  "cpf": {
    "section": 2,
    "field": 7
  },
  "type-official-document": {
    "section": 2,
    "field": 8
  },
  "document-number": {
    "section": 2,
    "field": 9
  },
  "official-document-file": {
    "section": 2,
    "field": 10
  },
  "nusp": {
    "section": 2,
    "field": 11
  },
  "phone-number": {
    "section": 2,
    "field": 12
  },
  "address": {
    "section": 2,
    "field": 13
  },
  "website": {
    "section": 2,
    "field": 14
  },
  "disabilities": {
    "section": 2,
    "field": 15
  },
  "disabilities-file": {
    "section": 2,
    "field": 16
  },
  "ethnicity-race": {
    "section": 2,
    "field": 17
  },
  "ethnicity-race-file": {
    "section": 2,
    "field": 18
  },
  "lattes-cv": {
    "section": 3,
    "field": 19
  },
  "lattes-cv-file": {
    "section": 3,
    "field": 20
  },
  "course-of-graduation": {
    "section": 3,
    "field": 21
  },
  "year-of-graduation": {
    "section": 3,
    "field": 22
  },
  "institution": {
    "section": 3,
    "field": 23
  },
  "country-undergraduate": {
    "section": 3,
    "field": 24
  },
  "studies-transcripts": {
    "section": 3,
    "field": 25
  },
  "year-poscomp": {
    "section": 3,
    "field": 26
  },
  "grades-poscomp": {
    "section": 3,
    "field": 27
  },
  "poscomp-file": {
    "section": 3,
    "field": 28
  },
  "graduate-courses-file": {
    "section": 3,
    "field": 29
  },
  "current-job": {
    "section": 4,
    "field": 30
  },
  "primary-area": {
    "section": 5,
    "field": 31
  },
  "secondary-area": {
    "section": 5,
    "field": 32
  },
  "motivation-letter": {
    "section": 5,
    "field": 33
  },
  "recommended-name-1": {
    "section": 5,
    "field": 34
  },
  "recommended-email-1": {
    "section": 5,
    "field": 35
  },
  "recommended-name-2": {
    "section": 5,
    "field": 36
  },
  "recommended-email-2": {
    "section": 5,
    "field": 37
  },
  "semester": {
    "section": 6,
    "field": 38
  },
  "intended-level": {
    "section": 6,
    "field": 39
  },
  "scholarship": {
    "section": 7,
    "field": 40
  },
  "relevant-information": {
    "section": 8,
    "field": 41
  },
  "about-this-program": {
    "section": 8,
    "field": 42
  },
  "name": {
    "section": 2,
    "field": 2
  },
  "gender": {
    "section": 2,
    "field": 5
  },
  "birth_date": {
    "section": 2,
    "field": 4
  },
  "phone_number": {
    "section": 2,
    "field": 12
  },
  "personal_website": {
    "section": 2,
    "field": 14
  },
  "lattes_curriculum": {
    "section": 3,
    "field": 19
  },
  "current_occupation": {
    "section": 4,
    "field": 30
  },
  "email": null,
  "graduation": {
    "year": {
      "section": 3,
      "field": 22
    },
    "course": {
      "section": 3,
      "field": 21
    },
    "country": {
      "section": 3,
      "field": 24
    },
    "institution": {
      "section": 3,
      "field": 23
    }
  },
  "poscomp": {
    "year": {
      "section": 3,
      "field": 26
    },
    "score": {
      "section": 3,
      "field": 27
    },
    "file": {
      "section": 3,
      "field": 28
    }
  },
  "research": {
    "field": {
      "primary": {
        "section": 5,
        "field": 31
      },
      "secondary": {
        "section": 5,
        "field": 32
      }
    },
    "program": null,
    "semester": {
      "section": 6,
      "field": 38
    },
    "dedication_level": {
      "section": 6,
      "field": 39
    },
    "will_apply_scholarship": {
      "section": 7,
      "field": 40
    }
  }
}$mapping$::jsonb,
    1, true, TIMESTAMPTZ '2026-10-16 00:00:00+00'),
    (2, 1, '2', 'recommender', 1,
    $mapping${
  "fullname-candidate": {
    "section": 9,
    "field": 43
  },
  "fullname": {
    "section": 9,
    "field": 44
  },
  "affiliation": {
    "section": 10,
    "field": 45
  },
  "known-time": {
    "section": 10,
    "field": 46
  },
  "relationship": {
    "section": 10,
    "field": 47
  },
  "rating": {
    "section": 10,
    "field": 48
  },
  "known_time": {
    "section": 10,
    "field": 46
  },
  "fullname_candidate": {
    "section": 9,
    "field": 43
  },
  "email": null
}$mapping$::jsonb,
    1, true, TIMESTAMPTZ '2026-10-16 00:00:00+00');

SELECT setval(pg_get_serial_sequence('edict', 'id'), (SELECT max(id) FROM edict));
SELECT setval(pg_get_serial_sequence('edict_phase', 'id'), (SELECT max(id) FROM edict_phase));
SELECT setval(pg_get_serial_sequence('edict_form_mappings', 'id'), (SELECT max(id) FROM edict_form_mappings));
