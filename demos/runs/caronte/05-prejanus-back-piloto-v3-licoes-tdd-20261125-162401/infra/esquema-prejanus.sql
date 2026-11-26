--
-- PostgreSQL database dump
--

\restrict fN4p90T6XoMxUmhNc4Yd6F0cEOEGNgUVjimurdNsCiJqUkmnpswIpWi1K4Q1nun

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
-- Name: form_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.form_type_enum AS ENUM (
    'candidate',
    'recommender'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: comment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.comment (
    id integer NOT NULL,
    user_id integer NOT NULL,
    submission_id integer NOT NULL,
    comment character varying NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: comment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.comment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: comment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.comment_id_seq OWNED BY public.comment.id;


--
-- Name: edict; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.edict (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying,
    candidate_forms character varying,
    recommenders_forms character varying,
    closed_date date NOT NULL,
    year integer NOT NULL,
    semester integer NOT NULL,
    type character varying NOT NULL,
    phase character varying NOT NULL,
    is_open boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    accept_forms character varying,
    user_id integer
);


--
-- Name: edict_form_mappings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.edict_form_mappings (
    id integer NOT NULL,
    edict_id integer NOT NULL,
    form_type public.form_type_enum NOT NULL,
    mapping jsonb NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    form_id character varying,
    user_id integer,
    form_version integer NOT NULL
);


--
-- Name: edict_form_mappings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edict_form_mappings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: edict_form_mappings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.edict_form_mappings_id_seq OWNED BY public.edict_form_mappings.id;


--
-- Name: edict_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edict_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: edict_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.edict_id_seq OWNED BY public.edict.id;


--
-- Name: edict_phase; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.edict_phase (
    id integer NOT NULL,
    edict_id integer NOT NULL,
    closed_date date,
    phase character varying NOT NULL
);


--
-- Name: edict_phase_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.edict_phase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: edict_phase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.edict_phase_id_seq OWNED BY public.edict_phase.id;


--
-- Name: favorites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.favorites (
    user_id integer NOT NULL,
    submission_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: labels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.labels (
    id integer NOT NULL,
    user_id integer NOT NULL,
    submission_id integer NOT NULL,
    label character varying NOT NULL,
    color character varying NOT NULL,
    context_type character varying
);


--
-- Name: labels_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.labels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: labels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.labels_id_seq OWNED BY public.labels.id;


--
-- Name: private_note; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.private_note (
    id integer NOT NULL,
    user_id integer NOT NULL,
    submission_id integer NOT NULL,
    note character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone
);


--
-- Name: private_note_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.private_note_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: private_note_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.private_note_id_seq OWNED BY public.private_note.id;


--
-- Name: submission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.submission (
    id integer NOT NULL,
    edict_id integer NOT NULL,
    advisor_id integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    candidate_form_id integer NOT NULL,
    recommenders_form_ids json,
    stats character varying DEFAULT 'underreview'::character varying NOT NULL,
    accept_form_id integer,
    entry_semester character varying,
    letter_sent boolean DEFAULT false NOT NULL,
    recommender_form_version integer NOT NULL,
    candidate_form_version integer NOT NULL
);


--
-- Name: submission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.submission_id_seq OWNED BY public.submission.id;


--
-- Name: submission_view; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.submission_view (
    id integer NOT NULL,
    user_id integer NOT NULL,
    submission_id integer NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: submission_view_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.submission_view_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: submission_view_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.submission_view_id_seq OWNED BY public.submission_view.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    email character varying NOT NULL,
    name character varying NOT NULL,
    role character varying NOT NULL,
    nusp character varying,
    research_field character varying,
    created_at timestamp with time zone
);


--
-- Name: user_edict_slots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_edict_slots (
    id integer NOT NULL,
    user_id integer NOT NULL,
    edict_id integer NOT NULL,
    slots integer
);


--
-- Name: user_edict_slots_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_edict_slots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_edict_slots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_edict_slots_id_seq OWNED BY public.user_edict_slots.id;


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: comment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment ALTER COLUMN id SET DEFAULT nextval('public.comment_id_seq'::regclass);


--
-- Name: edict id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict ALTER COLUMN id SET DEFAULT nextval('public.edict_id_seq'::regclass);


--
-- Name: edict_form_mappings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_form_mappings ALTER COLUMN id SET DEFAULT nextval('public.edict_form_mappings_id_seq'::regclass);


--
-- Name: edict_phase id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_phase ALTER COLUMN id SET DEFAULT nextval('public.edict_phase_id_seq'::regclass);


--
-- Name: labels id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.labels ALTER COLUMN id SET DEFAULT nextval('public.labels_id_seq'::regclass);


--
-- Name: private_note id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.private_note ALTER COLUMN id SET DEFAULT nextval('public.private_note_id_seq'::regclass);


--
-- Name: submission id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission ALTER COLUMN id SET DEFAULT nextval('public.submission_id_seq'::regclass);


--
-- Name: submission_view id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission_view ALTER COLUMN id SET DEFAULT nextval('public.submission_view_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: user_edict_slots id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_edict_slots ALTER COLUMN id SET DEFAULT nextval('public.user_edict_slots_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: comment comment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment
    ADD CONSTRAINT comment_pkey PRIMARY KEY (id);


--
-- Name: edict_form_mappings edict_form_mappings_edict_id_form_type_form_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_form_mappings
    ADD CONSTRAINT edict_form_mappings_edict_id_form_type_form_version_key UNIQUE (edict_id, form_type, form_version);


--
-- Name: edict_form_mappings edict_form_mappings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_form_mappings
    ADD CONSTRAINT edict_form_mappings_pkey PRIMARY KEY (id);


--
-- Name: edict_phase edict_phase_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_phase
    ADD CONSTRAINT edict_phase_pkey PRIMARY KEY (id);


--
-- Name: edict edict_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict
    ADD CONSTRAINT edict_pkey PRIMARY KEY (id);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (user_id, submission_id);


--
-- Name: labels labels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.labels
    ADD CONSTRAINT labels_pkey PRIMARY KEY (id);


--
-- Name: private_note private_note_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.private_note
    ADD CONSTRAINT private_note_pkey PRIMARY KEY (id);


--
-- Name: submission single_form_for_edict; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT single_form_for_edict UNIQUE (candidate_form_id, edict_id);


--
-- Name: submission submission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT submission_pkey PRIMARY KEY (id);


--
-- Name: submission_view submission_view_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission_view
    ADD CONSTRAINT submission_view_pkey PRIMARY KEY (id);


--
-- Name: user_edict_slots uq_user_edict; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_edict_slots
    ADD CONSTRAINT uq_user_edict UNIQUE (user_id, edict_id);


--
-- Name: private_note uq_user_submission_private_note; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.private_note
    ADD CONSTRAINT uq_user_submission_private_note UNIQUE (user_id, submission_id);


--
-- Name: user_edict_slots user_edict_slots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_edict_slots
    ADD CONSTRAINT user_edict_slots_pkey PRIMARY KEY (id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: comment comment_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment
    ADD CONSTRAINT comment_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submission(id) ON DELETE CASCADE;


--
-- Name: comment comment_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.comment
    ADD CONSTRAINT comment_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: edict_form_mappings edict_form_mappings_edict_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_form_mappings
    ADD CONSTRAINT edict_form_mappings_edict_id_fkey FOREIGN KEY (edict_id) REFERENCES public.edict(id) ON DELETE CASCADE;


--
-- Name: edict_form_mappings edict_form_mappings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_form_mappings
    ADD CONSTRAINT edict_form_mappings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: edict_phase edict_phase_edict_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict_phase
    ADD CONSTRAINT edict_phase_edict_id_fkey FOREIGN KEY (edict_id) REFERENCES public.edict(id) ON DELETE CASCADE;


--
-- Name: edict edict_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edict
    ADD CONSTRAINT edict_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE SET NULL;


--
-- Name: favorites favorites_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submission(id) ON DELETE CASCADE;


--
-- Name: favorites favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: labels labels_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.labels
    ADD CONSTRAINT labels_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submission(id) ON DELETE CASCADE;


--
-- Name: labels labels_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.labels
    ADD CONSTRAINT labels_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: private_note private_note_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.private_note
    ADD CONSTRAINT private_note_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submission(id) ON DELETE CASCADE;


--
-- Name: private_note private_note_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.private_note
    ADD CONSTRAINT private_note_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: submission submission_advisor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT submission_advisor_id_fkey FOREIGN KEY (advisor_id) REFERENCES public."user"(id) ON DELETE SET NULL;


--
-- Name: submission submission_edict_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT submission_edict_id_fkey FOREIGN KEY (edict_id) REFERENCES public.edict(id) ON DELETE CASCADE;


--
-- Name: submission_view submission_view_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission_view
    ADD CONSTRAINT submission_view_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submission(id) ON DELETE CASCADE;


--
-- Name: submission_view submission_view_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.submission_view
    ADD CONSTRAINT submission_view_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: user_edict_slots user_edict_slots_edict_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_edict_slots
    ADD CONSTRAINT user_edict_slots_edict_id_fkey FOREIGN KEY (edict_id) REFERENCES public.edict(id) ON DELETE CASCADE;


--
-- Name: user_edict_slots user_edict_slots_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_edict_slots
    ADD CONSTRAINT user_edict_slots_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict fN4p90T6XoMxUmhNc4Yd6F0cEOEGNgUVjimurdNsCiJqUkmnpswIpWi1K4Q1nun

