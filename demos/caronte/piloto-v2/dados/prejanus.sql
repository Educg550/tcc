--
-- PostgreSQL database dump
--

\restrict QNW0F69VnbyHb72NdgjFdoKLrGbY7PJ50XijTuqiHFmKuE0Sl3AnFdLxFClpJxj

-- Dumped from database version 17.6 (Debian 17.6-2.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-2.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public."user" (id, email, name, role, nusp, research_field, created_at) VALUES (1, 'admin.piloto@example.com', 'Admin Piloto', 'administrator', '900001', NULL, NULL);
INSERT INTO public."user" (id, email, name, role, nusp, research_field, created_at) VALUES (2, 'docente.piloto@example.com', 'Docente Piloto', 'teacher', '900002', NULL, NULL);
INSERT INTO public."user" (id, email, name, role, nusp, research_field, created_at) VALUES (3, 'outra.piloto@example.com', 'Outra Docente', 'teacher', '900003', NULL, NULL);
INSERT INTO public."user" (id, email, name, role, nusp, research_field, created_at) VALUES (4, 'secretaria.piloto@example.com', 'Secretaria Piloto', 'secretary', '900004', NULL, NULL);
INSERT INTO public."user" (id, email, name, role, nusp, research_field, created_at) VALUES (5, 'coordenador.piloto@example.com', 'Coordenador Piloto', 'coordinator', '900005', NULL, NULL);
INSERT INTO public."user" (id, email, name, role, nusp, research_field, created_at) VALUES (6, 'estudante.piloto@example.com', 'Estudante Piloto', 'student', '900006', NULL, NULL);


--
-- Data for Name: edict; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.edict (id, title, description, candidate_forms, recommenders_forms, closed_date, year, semester, type, phase, is_open, created_at, updated_at, accept_forms, user_id) VALUES (1, 'Piloto TCC - Mestrado 2026', 'Fixture do piloto Caronte', '1', '2', '2030-04-01', 2026, 1, 'mestrado', 'avaliacao', true, '2026-10-16 00:00:00+00', NULL, '4', 1);
INSERT INTO public.edict (id, title, description, candidate_forms, recommenders_forms, closed_date, year, semester, type, phase, is_open, created_at, updated_at, accept_forms, user_id) VALUES (2, 'Piloto v2 - Doutorado', 'Edital doutorado', '3', '2', '2030-04-01', 2026, 2, 'doutorado', 'avaliacao', true, NULL, NULL, '4', 1);
INSERT INTO public.edict (id, title, description, candidate_forms, recommenders_forms, closed_date, year, semester, type, phase, is_open, created_at, updated_at, accept_forms, user_id) VALUES (3, 'Piloto v2 - Mestrado PPI', 'Edital com PPI mapeado', '1', '2', '2030-04-01', 2026, 1, 'mestrado', 'avaliacao', true, NULL, NULL, '4', 1);


--
-- Data for Name: submission; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (1, 1, NULL, '2026-10-16 12:00:00+00', NULL, 1, '[]', 'underreview', NULL, 'Primeiro semestre.', false, 1, 1);
INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (2, 1, NULL, NULL, NULL, 2, NULL, 'underreview', NULL, NULL, false, 1, 2);
INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (3, 2, NULL, NULL, NULL, 3, NULL, 'underreview', NULL, NULL, false, 1, 1);
INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (4, 1, NULL, NULL, NULL, 7, NULL, 'underreview', NULL, NULL, false, 1, 2);
INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (5, 3, NULL, NULL, NULL, 1, NULL, 'underreview', NULL, NULL, false, 1, 1);
INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (6, 3, NULL, NULL, NULL, 2, NULL, 'underreview', NULL, NULL, false, 1, 2);
INSERT INTO public.submission (id, edict_id, advisor_id, created_at, updated_at, candidate_form_id, recommenders_form_ids, stats, accept_form_id, entry_semester, letter_sent, recommender_form_version, candidate_form_version) VALUES (8, 3, NULL, NULL, NULL, 7, NULL, 'underreview', NULL, NULL, false, 1, 2);


--
-- Data for Name: comment; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: edict_form_mappings; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (1, 1, 'candidate', '{"cpf": {"field": 7, "section": 2}, "name": {"field": 2, "section": 2}, "nusp": {"field": 11, "section": 2}, "birth": {"field": 4, "section": 2}, "email": null, "gender": {"field": 5, "section": 2}, "address": {"field": 13, "section": 2}, "poscomp": {"file": {"field": 28, "section": 3}, "year": {"field": 26, "section": 3}, "score": {"field": 27, "section": 3}}, "website": {"field": 14, "section": 2}, "fullname": {"field": 2, "section": 2}, "research": {"field": {"primary": {"field": 31, "section": 5}, "secondary": {"field": 32, "section": 5}}, "program": null, "semester": {"field": 38, "section": 6}, "dedication_level": {"field": 39, "section": 6}, "will_apply_scholarship": {"field": 40, "section": 7}}, "semester": {"field": 38, "section": 6}, "lattes-cv": {"field": 19, "section": 3}, "birth_date": {"field": 4, "section": 2}, "graduation": {"year": {"field": 22, "section": 3}, "course": {"field": 21, "section": 3}, "country": {"field": 24, "section": 3}, "institution": {"field": 23, "section": 3}}, "current-job": {"field": 30, "section": 4}, "institution": {"field": 23, "section": 3}, "nationality": {"field": 6, "section": 2}, "scholarship": {"field": 40, "section": 7}, "disabilities": {"field": 15, "section": 2}, "phone-number": {"field": 12, "section": 2}, "phone_number": {"field": 12, "section": 2}, "poscomp-file": {"field": 28, "section": 3}, "primary-area": {"field": 31, "section": 5}, "year-poscomp": {"field": 26, "section": 3}, "acknowledgment": {"field": 1, "section": 1}, "biological-sex": {"field": 5, "section": 2}, "ethnicity-race": null, "grades-poscomp": {"field": 27, "section": 3}, "intended-level": {"field": 39, "section": 6}, "lattes-cv-file": {"field": 20, "section": 3}, "secondary-area": {"field": 32, "section": 5}, "document-number": {"field": 9, "section": 2}, "mother-fullname": {"field": 3, "section": 2}, "personal_website": {"field": 14, "section": 2}, "disabilities-file": {"field": 16, "section": 2}, "lattes_curriculum": {"field": 19, "section": 3}, "motivation-letter": {"field": 33, "section": 5}, "about-this-program": {"field": 42, "section": 8}, "current_occupation": {"field": 30, "section": 4}, "recommended-name-1": {"field": 34, "section": 5}, "recommended-name-2": {"field": 36, "section": 5}, "year-of-graduation": {"field": 22, "section": 3}, "ethnicity-race-file": {"field": 18, "section": 2}, "recommended-email-1": {"field": 35, "section": 5}, "recommended-email-2": {"field": 37, "section": 5}, "studies-transcripts": {"field": 25, "section": 3}, "course-of-graduation": {"field": 21, "section": 3}, "relevant-information": {"field": 41, "section": 8}, "country-undergraduate": {"field": 24, "section": 3}, "graduate-courses-file": {"field": 29, "section": 3}, "official-document-file": {"field": 10, "section": 2}, "type-official-document": {"field": 8, "section": 2}}', true, '2026-10-16 00:00:00+00', '1', 1, 1);
INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (2, 1, 'recommender', '{"email": null, "rating": {"field": 48, "section": 10}, "fullname": {"field": 44, "section": 9}, "known-time": {"field": 46, "section": 10}, "known_time": {"field": 46, "section": 10}, "affiliation": {"field": 45, "section": 10}, "relationship": {"field": 47, "section": 10}, "fullname-candidate": {"field": 43, "section": 9}, "fullname_candidate": {"field": 43, "section": 9}}', true, '2026-10-16 00:00:00+00', '2', 1, 1);
INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (3, 1, 'candidate', '{"cpf": {"field": 1007, "section": 102}, "name": {"field": 1002, "section": 102}, "nusp": {"field": 1011, "section": 102}, "birth": {"field": 1004, "section": 102}, "email": null, "gender": {"field": 1005, "section": 102}, "address": {"field": 1013, "section": 102}, "poscomp": {"file": {"field": 1028, "section": 103}, "year": {"field": 1026, "section": 103}, "score": {"field": 1027, "section": 103}}, "website": {"field": 1014, "section": 102}, "fullname": {"field": 1002, "section": 102}, "research": {"field": {"primary": {"field": 1031, "section": 105}, "secondary": {"field": 1032, "section": 105}}, "program": null, "semester": {"field": 1038, "section": 106}, "dedication_level": {"field": 1039, "section": 106}, "will_apply_scholarship": {"field": 1040, "section": 107}}, "semester": {"field": 1038, "section": 106}, "lattes-cv": {"field": 1019, "section": 103}, "birth_date": {"field": 1004, "section": 102}, "graduation": {"year": {"field": 1022, "section": 103}, "course": {"field": 1021, "section": 103}, "country": {"field": 1024, "section": 103}, "institution": {"field": 1023, "section": 103}}, "current-job": {"field": 1030, "section": 104}, "institution": {"field": 1023, "section": 103}, "nationality": {"field": 1006, "section": 102}, "scholarship": {"field": 1040, "section": 107}, "disabilities": {"field": 1015, "section": 102}, "phone-number": {"field": 1012, "section": 102}, "phone_number": {"field": 1012, "section": 102}, "poscomp-file": {"field": 1028, "section": 103}, "primary-area": {"field": 1031, "section": 105}, "year-poscomp": {"field": 1026, "section": 103}, "acknowledgment": {"field": 1001, "section": 101}, "biological-sex": {"field": 1005, "section": 102}, "ethnicity-race": null, "grades-poscomp": {"field": 1027, "section": 103}, "intended-level": {"field": 1039, "section": 106}, "lattes-cv-file": {"field": 1020, "section": 103}, "secondary-area": {"field": 1032, "section": 105}, "document-number": {"field": 1009, "section": 102}, "mother-fullname": {"field": 1003, "section": 102}, "personal_website": {"field": 1014, "section": 102}, "disabilities-file": {"field": 1016, "section": 102}, "lattes_curriculum": {"field": 1019, "section": 103}, "motivation-letter": {"field": 1033, "section": 105}, "about-this-program": {"field": 1042, "section": 108}, "current_occupation": {"field": 1030, "section": 104}, "recommended-name-1": {"field": 1034, "section": 105}, "recommended-name-2": {"field": 1036, "section": 105}, "year-of-graduation": {"field": 1022, "section": 103}, "ethnicity-race-file": {"field": 1018, "section": 102}, "recommended-email-1": {"field": 1035, "section": 105}, "recommended-email-2": {"field": 1037, "section": 105}, "studies-transcripts": {"field": 1025, "section": 103}, "course-of-graduation": {"field": 1021, "section": 103}, "relevant-information": {"field": 1041, "section": 108}, "country-undergraduate": {"field": 1024, "section": 103}, "graduate-courses-file": {"field": 1029, "section": 103}, "official-document-file": {"field": 1010, "section": 102}, "type-official-document": {"field": 1008, "section": 102}}', true, '2026-10-17 14:42:34.951505+00', '1', 1, 2);
INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (4, 2, 'candidate', '{"cpf": null, "name": {"field": 51, "section": 13}, "nusp": null, "birth": {"field": 52, "section": 13}, "email": null, "gender": null, "address": {"field": 56, "section": 13}, "poscomp": {"file": {"field": 70, "section": 14}, "year": {"field": 68, "section": 14}, "score": {"field": 69, "section": 14}}, "website": {"field": 58, "section": 13}, "fullname": {"field": 51, "section": 13}, "research": {"field": {"primary": {"field": 73, "section": 16}, "secondary": {"field": 74, "section": 16}}, "program": null, "semester": null, "dedication_level": null, "will_apply_scholarship": {"field": 76, "section": 16}}, "semester": null, "lattes-cv": {"field": 59, "section": 14}, "birth_date": {"field": 52, "section": 13}, "graduation": {"year": null, "course": {"field": 61, "section": 14}, "country": null, "institution": null}, "current-job": {"field": 72, "section": 15}, "institution": null, "nationality": {"field": 54, "section": 13}, "scholarship": {"field": 76, "section": 16}, "disabilities": null, "phone-number": {"field": 57, "section": 13}, "phone_number": {"field": 57, "section": 13}, "poscomp-file": {"field": 70, "section": 14}, "primary-area": {"field": 73, "section": 16}, "year-poscomp": {"field": 68, "section": 14}, "acknowledgment": {"field": 49, "section": 11}, "biological-sex": null, "ethnicity-race": null, "grades-poscomp": {"field": 69, "section": 14}, "intended-level": null, "lattes-cv-file": {"field": 60, "section": 14}, "secondary-area": {"field": 74, "section": 16}, "document-number": null, "mother-fullname": {"field": 53, "section": 13}, "personal_website": {"field": 58, "section": 13}, "disabilities-file": null, "lattes_curriculum": {"field": 59, "section": 14}, "motivation-letter": {"field": 75, "section": 16}, "about-this-program": null, "current_occupation": {"field": 72, "section": 15}, "recommended-name-1": null, "recommended-name-2": null, "year-of-graduation": null, "ethnicity-race-file": null, "recommended-email-1": null, "recommended-email-2": null, "studies-transcripts": {"field": 63, "section": 14}, "course-of-graduation": {"field": 61, "section": 14}, "relevant-information": {"field": 79, "section": 17}, "country-undergraduate": null, "graduate-courses-file": null, "official-document-file": null, "type-official-document": null}', true, '2026-10-17 14:42:34.951505+00', '3', 1, 1);
INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (5, 3, 'candidate', '{"cpf": {"field": 7, "section": 2}, "name": {"field": 2, "section": 2}, "nusp": {"field": 11, "section": 2}, "birth": {"field": 4, "section": 2}, "email": null, "gender": {"field": 5, "section": 2}, "address": {"field": 13, "section": 2}, "poscomp": {"file": {"field": 28, "section": 3}, "year": {"field": 26, "section": 3}, "score": {"field": 27, "section": 3}}, "website": {"field": 14, "section": 2}, "fullname": {"field": 2, "section": 2}, "research": {"field": {"primary": {"field": 31, "section": 5}, "secondary": {"field": 32, "section": 5}}, "program": null, "semester": {"field": 38, "section": 6}, "dedication_level": {"field": 39, "section": 6}, "will_apply_scholarship": {"field": 40, "section": 7}}, "semester": {"field": 38, "section": 6}, "lattes-cv": {"field": 19, "section": 3}, "birth_date": {"field": 4, "section": 2}, "graduation": {"year": {"field": 22, "section": 3}, "course": {"field": 21, "section": 3}, "country": {"field": 24, "section": 3}, "institution": {"field": 23, "section": 3}}, "current-job": {"field": 30, "section": 4}, "institution": {"field": 23, "section": 3}, "nationality": {"field": 6, "section": 2}, "scholarship": {"field": 40, "section": 7}, "disabilities": {"field": 15, "section": 2}, "phone-number": {"field": 12, "section": 2}, "phone_number": {"field": 12, "section": 2}, "poscomp-file": {"field": 28, "section": 3}, "primary-area": {"field": 31, "section": 5}, "year-poscomp": {"field": 26, "section": 3}, "acknowledgment": {"field": 1, "section": 1}, "biological-sex": {"field": 5, "section": 2}, "ethnicity-race": {"field": 17, "section": 2}, "grades-poscomp": {"field": 27, "section": 3}, "intended-level": {"field": 39, "section": 6}, "lattes-cv-file": {"field": 20, "section": 3}, "secondary-area": {"field": 32, "section": 5}, "document-number": {"field": 9, "section": 2}, "mother-fullname": {"field": 3, "section": 2}, "personal_website": {"field": 14, "section": 2}, "disabilities-file": {"field": 16, "section": 2}, "lattes_curriculum": {"field": 19, "section": 3}, "motivation-letter": {"field": 33, "section": 5}, "about-this-program": {"field": 42, "section": 8}, "current_occupation": {"field": 30, "section": 4}, "recommended-name-1": {"field": 34, "section": 5}, "recommended-name-2": {"field": 36, "section": 5}, "year-of-graduation": {"field": 22, "section": 3}, "ethnicity-race-file": {"field": 18, "section": 2}, "recommended-email-1": {"field": 35, "section": 5}, "recommended-email-2": {"field": 37, "section": 5}, "studies-transcripts": {"field": 25, "section": 3}, "course-of-graduation": {"field": 21, "section": 3}, "relevant-information": {"field": 41, "section": 8}, "country-undergraduate": {"field": 24, "section": 3}, "graduate-courses-file": {"field": 29, "section": 3}, "official-document-file": {"field": 10, "section": 2}, "type-official-document": {"field": 8, "section": 2}}', true, '2026-10-17 14:42:34.951505+00', '1', 1, 1);
INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (6, 3, 'recommender', '{"email": null, "rating": {"field": 48, "section": 10}, "fullname": {"field": 44, "section": 9}, "known-time": {"field": 46, "section": 10}, "known_time": {"field": 46, "section": 10}, "affiliation": {"field": 45, "section": 10}, "relationship": {"field": 47, "section": 10}, "fullname-candidate": {"field": 43, "section": 9}, "fullname_candidate": {"field": 43, "section": 9}}', true, '2026-10-17 14:42:34.951505+00', '2', 1, 1);
INSERT INTO public.edict_form_mappings (id, edict_id, form_type, mapping, is_active, created_at, form_id, user_id, form_version) VALUES (7, 3, 'candidate', '{"cpf": {"field": 1007, "section": 102}, "name": {"field": 1002, "section": 102}, "nusp": {"field": 1011, "section": 102}, "birth": {"field": 1004, "section": 102}, "email": null, "gender": {"field": 1005, "section": 102}, "address": {"field": 1013, "section": 102}, "poscomp": {"file": {"field": 1028, "section": 103}, "year": {"field": 1026, "section": 103}, "score": {"field": 1027, "section": 103}}, "website": {"field": 1014, "section": 102}, "fullname": {"field": 1002, "section": 102}, "research": {"field": {"primary": {"field": 1031, "section": 105}, "secondary": {"field": 1032, "section": 105}}, "program": null, "semester": {"field": 1038, "section": 106}, "dedication_level": {"field": 1039, "section": 106}, "will_apply_scholarship": {"field": 1040, "section": 107}}, "semester": {"field": 1038, "section": 106}, "lattes-cv": {"field": 1019, "section": 103}, "birth_date": {"field": 1004, "section": 102}, "graduation": {"year": {"field": 1022, "section": 103}, "course": {"field": 1021, "section": 103}, "country": {"field": 1024, "section": 103}, "institution": {"field": 1023, "section": 103}}, "current-job": {"field": 1030, "section": 104}, "institution": {"field": 1023, "section": 103}, "nationality": {"field": 1006, "section": 102}, "scholarship": {"field": 1040, "section": 107}, "disabilities": {"field": 1015, "section": 102}, "phone-number": {"field": 1012, "section": 102}, "phone_number": {"field": 1012, "section": 102}, "poscomp-file": {"field": 1028, "section": 103}, "primary-area": {"field": 1031, "section": 105}, "year-poscomp": {"field": 1026, "section": 103}, "acknowledgment": {"field": 1001, "section": 101}, "biological-sex": {"field": 1005, "section": 102}, "ethnicity-race": {"field": 1017, "section": 102}, "grades-poscomp": {"field": 1027, "section": 103}, "intended-level": {"field": 1039, "section": 106}, "lattes-cv-file": {"field": 1020, "section": 103}, "secondary-area": {"field": 1032, "section": 105}, "document-number": {"field": 1009, "section": 102}, "mother-fullname": {"field": 1003, "section": 102}, "personal_website": {"field": 1014, "section": 102}, "disabilities-file": {"field": 1016, "section": 102}, "lattes_curriculum": {"field": 1019, "section": 103}, "motivation-letter": {"field": 1033, "section": 105}, "about-this-program": {"field": 1042, "section": 108}, "current_occupation": {"field": 1030, "section": 104}, "recommended-name-1": {"field": 1034, "section": 105}, "recommended-name-2": {"field": 1036, "section": 105}, "year-of-graduation": {"field": 1022, "section": 103}, "ethnicity-race-file": {"field": 1018, "section": 102}, "recommended-email-1": {"field": 1035, "section": 105}, "recommended-email-2": {"field": 1037, "section": 105}, "studies-transcripts": {"field": 1025, "section": 103}, "course-of-graduation": {"field": 1021, "section": 103}, "relevant-information": {"field": 1041, "section": 108}, "country-undergraduate": {"field": 1024, "section": 103}, "graduate-courses-file": {"field": 1029, "section": 103}, "official-document-file": {"field": 1010, "section": 102}, "type-official-document": {"field": 1008, "section": 102}}', true, '2026-10-17 14:42:34.951505+00', '1', 1, 2);


--
-- Data for Name: edict_phase; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (1, 1, '2030-01-01', 'inscricoes');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (2, 1, '2030-02-01', 'homologacao');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (3, 1, '2030-03-01', 'avaliacao');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (4, 1, '2030-04-01', 'encerrado');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (5, 2, '2030-01-01', 'inscricoes');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (6, 2, '2030-02-01', 'homologacao');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (7, 2, '2030-03-01', 'avaliacao');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (8, 2, '2030-04-01', 'encerrado');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (9, 3, '2030-01-01', 'inscricoes');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (10, 3, '2030-02-01', 'homologacao');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (11, 3, '2030-03-01', 'avaliacao');
INSERT INTO public.edict_phase (id, edict_id, closed_date, phase) VALUES (12, 3, '2030-04-01', 'encerrado');


--
-- Data for Name: favorites; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: labels; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: private_note; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: submission_view; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: user_edict_slots; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Name: comment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.comment_id_seq', 1, false);


--
-- Name: edict_form_mappings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edict_form_mappings_id_seq', 7, true);


--
-- Name: edict_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edict_id_seq', 3, true);


--
-- Name: edict_phase_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.edict_phase_id_seq', 12, true);


--
-- Name: labels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.labels_id_seq', 1, false);


--
-- Name: private_note_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.private_note_id_seq', 1, false);


--
-- Name: submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.submission_id_seq', 8, true);


--
-- Name: submission_view_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.submission_view_id_seq', 1, false);


--
-- Name: user_edict_slots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_edict_slots_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 6, true);


--
-- PostgreSQL database dump complete
--

\unrestrict QNW0F69VnbyHb72NdgjFdoKLrGbY7PJ50XijTuqiHFmKuE0Sl3AnFdLxFClpJxj

