--
-- PostgreSQL database dump
--

\restrict 1lgLAP7AhZNCpETgNewZpgl00BSCIXO7dC6oR8EgdnbndDggYzuuOgmpBlFD7VH

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
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: field_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.field_type AS ENUM (
    'Text',
    'LongText',
    'Number',
    'CheckBox',
    'Radio',
    'Date',
    'File'
);


--
-- Name: form_phase; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.form_phase AS ENUM (
    'Registration',
    'Approval',
    'Completed'
);


--
-- Name: change_form_phase(integer, public.form_phase); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.change_form_phase(p_id integer, p_phase public.form_phase) RETURNS TABLE(id integer, phase public.form_phase)
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
            begin
                return query
                update form
                    set phase = p_phase
                where form.id = p_id
                returning form.id, form.phase;
            end;
            $$;


--
-- Name: get_all_submissions(integer, integer, integer, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_all_submissions(p_form_id integer, p_order_by integer DEFAULT 0, p_order_type integer DEFAULT 0, p_search text DEFAULT ''::text, p_lang text DEFAULT 'pt'::text) RETURNS TABLE(id integer, token uuid, submitted_at timestamp without time zone, metadata jsonb, email text, responses jsonb)
    LANGUAGE plpgsql
    AS $_$
declare
    order_columns text[] := array['id', 'submitted_at', 'email'];
    order_directions text[] := array['desc', 'asc'];
    order_column text;
    order_direction text;
begin 
    if p_order_by < 0 or p_order_by >= array_length(order_columns, 1) then
        raise exception 'Invalid order_by index';
    end if;
    if p_order_type < 0 OR p_order_type >= array_length(order_directions, 1) then
        raise exception 'Invalid order_type index';
    end if;

    order_column := order_columns[p_order_by + 1];
    order_direction := order_directions[p_order_type + 1];

    return query execute format(
        $f$
        select
            form_response.id,
            form_response.token,
            form_response.submitted_at,
            form_response.metadata,
            form_response.email,
            json_agg(
                json_build_object(
                    form_field.name, json_build_object(
                        'label', coalesce(form_field.label ->> %L, form_field.label ->> 'pt'),
                        'value', r.value
                    )
                )
            )::jsonb as responses
        from form_response
        inner join responses r
            on form_response.id = r.response_id
            and unaccent(r.value) ilike unaccent(%L)
        inner join form_field
            on r.field_id = form_field.id
        inner join form f
            on f.id = form_response.form_id
        where form_response.form_id = %s
            and form_response.submitted_at is not null  -- para nao pegar respostas em andamento
        group by form_response.id
        order by %I %s, form_response.id DESC
        $f$,
        p_lang,
        '%' || p_search || '%',
        p_form_id,
        order_column,
        order_direction
    );
end;
$_$;


--
-- Name: get_all_user_forms(integer, integer, integer, jsonb, text, text, boolean); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_all_user_forms(p_user_id integer DEFAULT NULL::integer, p_order_by integer DEFAULT 0, p_order_type integer DEFAULT 0, p_tag_filter jsonb DEFAULT NULL::jsonb, p_search text DEFAULT ''::text, p_lang text DEFAULT 'pt'::text, p_is_admin boolean DEFAULT false) RETURNS TABLE(id integer, title text, created_at timestamp without time zone, created_by text, tags jsonb, phase public.form_phase)
    LANGUAGE plpgsql
    AS $_$
declare
    order_columns text[] := array['id', 'title', 'created_at'];
    order_directions text[] := array['desc', 'asc'];
    order_column text;
    order_direction text;
    condition text := '';
    key text;
    value text;
    user_filter text := '';
begin
    if p_user_id is not null then
        select role = 'administrator' into p_is_admin
        from users
        where users.id = p_user_id;
    end if;
              
    if p_order_by < 0 or p_order_by >= array_length(order_columns, 1) then
        raise exception 'Invalid order_by index';
    end if;
    if p_order_type < 0 OR p_order_type >= array_length(order_directions, 1) then
        raise exception 'Invalid order_type index';
    end if;

    order_column := order_columns[p_order_by + 1];
    order_direction := order_directions[p_order_type + 1];

    if p_tag_filter is not null then
        for key, value in select * from jsonb_each_text(p_tag_filter)
        loop
            if value is not null and value <> '' then
                condition := condition || format(' and form.tags ->> unaccent(%L) ilike unaccent(%L)', key, '%' || value || '%');
            end if;
        end loop;
    end if;
              
    user_filter := case when p_is_admin then '' else format(' and (form.created_by = %s or form_collaborators.user_id = %s)', p_user_id, p_user_id) end;

    return query execute format($q$
        select 
            form.id, 
            coalesce(form.title ->> %L, form.title ->> 'pt') as title,
            form.created_at,
            users.email as created_by,
            form.tags,
            form.phase
        from form
            left join users on form.created_by = users.id
            left join form_collaborators on form.id = form_collaborators.form_id
        where 
            unaccent(coalesce(form.title ->> %L, form.title ->> 'pt')) ilike unaccent(%L)
            %s
            %s
            order by %I %s
    $q$, p_lang, p_lang, '%' || p_search || '%', user_filter, condition, order_column, order_direction);
end;
$_$;


--
-- Name: get_submissions_by_id(integer, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_submissions_by_id(p_response_id integer, p_lang text DEFAULT 'pt'::text) RETURNS TABLE(id integer, token uuid, submitted_at timestamp without time zone, metadata jsonb, email text, responses jsonb)
    LANGUAGE plpgsql
    AS $_$
begin
    return query execute format(
        $f$
        select
            form_response.id,
            form_response.token,
            form_response.submitted_at,
            form_response.metadata,
            form_response.email,
            json_agg(
                json_build_object(
                    form_field.name, json_build_object(
                        'label', coalesce(form_field.label ->> %L, form_field.label ->> 'pt'),
                        'value', r.value
                    )
                )
            )::jsonb as responses
        from form_response
        inner join responses r
            on form_response.id = r.response_id
        inner join form_field
            on r.field_id = form_field.id
        where 
            form_response.id = %s
            and form_response.submitted_at is not null  -- para nao pegar respostas em andamento
        group by form_response.id
        order by form_response.id DESC
        $f$,
        p_lang,
        p_response_id
    );
end;
$_$;


--
-- Name: update_form_response_section(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_form_response_section(p_id integer, p_current_section integer) RETURNS TABLE(id integer, current_section integer)
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
            begin
                return query
                update form_response
                    set current_section = p_current_section
                where form_response.id = p_id
                returning form_response.id, form_response.current_section;
            end;
            $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: field_option; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.field_option (
    id integer NOT NULL,
    field_id integer,
    value jsonb DEFAULT '{}'::jsonb NOT NULL,
    metadata jsonb
);


--
-- Name: field_option_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.field_option_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: field_option_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.field_option_id_seq OWNED BY public.field_option.id;


--
-- Name: form; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form (
    id integer NOT NULL,
    title jsonb DEFAULT '{}'::jsonb NOT NULL,
    description jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp without time zone,
    phase public.form_phase DEFAULT 'Registration'::public.form_phase NOT NULL,
    created_by integer,
    tags jsonb DEFAULT '{}'::jsonb NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    version integer DEFAULT 1 NOT NULL
);


--
-- Name: form_collaborators; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form_collaborators (
    id integer NOT NULL,
    form_id integer,
    user_id integer,
    can_edit boolean DEFAULT true,
    invited_by integer,
    invited_at timestamp without time zone DEFAULT now()
);


--
-- Name: form_collaborators_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.form_collaborators_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: form_collaborators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.form_collaborators_id_seq OWNED BY public.form_collaborators.id;


--
-- Name: form_field; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form_field (
    id integer NOT NULL,
    form_id integer,
    section_id integer,
    label jsonb DEFAULT '{}'::jsonb NOT NULL,
    name text NOT NULL,
    description jsonb DEFAULT '{}'::jsonb NOT NULL,
    type public.field_type NOT NULL,
    placeholder text,
    required boolean DEFAULT false,
    disabled boolean DEFAULT false,
    validation text,
    error_message jsonb DEFAULT '{}'::jsonb NOT NULL,
    prefix text,
    "position" integer DEFAULT 0,
    is_active boolean DEFAULT true NOT NULL,
    version integer DEFAULT 1 NOT NULL
);


--
-- Name: form_field_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.form_field_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: form_field_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.form_field_id_seq OWNED BY public.form_field.id;


--
-- Name: form_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.form_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: form_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.form_id_seq OWNED BY public.form.id;


--
-- Name: form_response; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form_response (
    id integer NOT NULL,
    form_id integer,
    shared_id integer,
    user_id integer,
    email text,
    token uuid NOT NULL,
    current_section integer DEFAULT 0,
    submitted_at timestamp without time zone,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    form_version integer DEFAULT 1 NOT NULL
);


--
-- Name: form_response_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.form_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: form_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.form_response_id_seq OWNED BY public.form_response.id;


--
-- Name: form_section; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form_section (
    id integer NOT NULL,
    form_id integer,
    title jsonb DEFAULT '{}'::jsonb NOT NULL,
    description jsonb DEFAULT '{}'::jsonb NOT NULL,
    "position" integer DEFAULT 0,
    is_active boolean DEFAULT true NOT NULL,
    version integer DEFAULT 1 NOT NULL
);


--
-- Name: form_section_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.form_section_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: form_section_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.form_section_id_seq OWNED BY public.form_section.id;


--
-- Name: form_shared; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.form_shared (
    id integer NOT NULL,
    form_id integer,
    unique_answers boolean DEFAULT false,
    is_public boolean DEFAULT false,
    token uuid NOT NULL,
    created_at timestamp without time zone,
    expiration_at timestamp without time zone
);


--
-- Name: form_shared_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.form_shared_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: form_shared_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.form_shared_id_seq OWNED BY public.form_shared.id;


--
-- Name: responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.responses (
    id integer NOT NULL,
    response_id integer,
    field_id integer,
    value text
);


--
-- Name: responses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.responses_id_seq OWNED BY public.responses.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email text NOT NULL,
    created_at timestamp without time zone,
    role text DEFAULT 'common'::text
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: field_option id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_option ALTER COLUMN id SET DEFAULT nextval('public.field_option_id_seq'::regclass);


--
-- Name: form id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form ALTER COLUMN id SET DEFAULT nextval('public.form_id_seq'::regclass);


--
-- Name: form_collaborators id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_collaborators ALTER COLUMN id SET DEFAULT nextval('public.form_collaborators_id_seq'::regclass);


--
-- Name: form_field id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_field ALTER COLUMN id SET DEFAULT nextval('public.form_field_id_seq'::regclass);


--
-- Name: form_response id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_response ALTER COLUMN id SET DEFAULT nextval('public.form_response_id_seq'::regclass);


--
-- Name: form_section id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_section ALTER COLUMN id SET DEFAULT nextval('public.form_section_id_seq'::regclass);


--
-- Name: form_shared id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_shared ALTER COLUMN id SET DEFAULT nextval('public.form_shared_id_seq'::regclass);


--
-- Name: responses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responses ALTER COLUMN id SET DEFAULT nextval('public.responses_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: field_option field_option_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_option
    ADD CONSTRAINT field_option_pkey PRIMARY KEY (id);


--
-- Name: form_collaborators form_collaborators_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_collaborators
    ADD CONSTRAINT form_collaborators_pkey PRIMARY KEY (id);


--
-- Name: form_field form_field_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_field
    ADD CONSTRAINT form_field_pkey PRIMARY KEY (id);


--
-- Name: form form_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form
    ADD CONSTRAINT form_pkey PRIMARY KEY (id);


--
-- Name: form_response form_response_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_response
    ADD CONSTRAINT form_response_pkey PRIMARY KEY (id);


--
-- Name: form_response form_response_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_response
    ADD CONSTRAINT form_response_token_key UNIQUE (token);


--
-- Name: form_section form_section_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_section
    ADD CONSTRAINT form_section_pkey PRIMARY KEY (id);


--
-- Name: form_shared form_shared_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_shared
    ADD CONSTRAINT form_shared_pkey PRIMARY KEY (id);


--
-- Name: form_shared form_shared_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_shared
    ADD CONSTRAINT form_shared_token_key UNIQUE (token);


--
-- Name: form_collaborators form_user_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_collaborators
    ADD CONSTRAINT form_user_unique UNIQUE (form_id, user_id);


--
-- Name: responses responses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_pkey PRIMARY KEY (id);


--
-- Name: responses responses_response_id_field_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_response_id_field_id_key UNIQUE (response_id, field_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: unique_form_name_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX unique_form_name_active ON public.form_field USING btree (form_id, name) WHERE (is_active = true);


--
-- Name: field_option field_option_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_option
    ADD CONSTRAINT field_option_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.form_field(id) ON DELETE CASCADE;


--
-- Name: form_collaborators form_collaborators_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_collaborators
    ADD CONSTRAINT form_collaborators_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.form(id) ON DELETE CASCADE;


--
-- Name: form_collaborators form_collaborators_invited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_collaborators
    ADD CONSTRAINT form_collaborators_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: form_collaborators form_collaborators_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_collaborators
    ADD CONSTRAINT form_collaborators_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: form form_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form
    ADD CONSTRAINT form_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: form_field form_field_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_field
    ADD CONSTRAINT form_field_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.form(id) ON DELETE CASCADE;


--
-- Name: form_field form_field_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_field
    ADD CONSTRAINT form_field_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.form_section(id) ON DELETE SET NULL;


--
-- Name: form_response form_response_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_response
    ADD CONSTRAINT form_response_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.form(id) ON DELETE CASCADE;


--
-- Name: form_response form_response_shared_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_response
    ADD CONSTRAINT form_response_shared_id_fkey FOREIGN KEY (shared_id) REFERENCES public.form_shared(id) ON DELETE SET NULL;


--
-- Name: form_response form_response_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_response
    ADD CONSTRAINT form_response_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: form_section form_section_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_section
    ADD CONSTRAINT form_section_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.form(id) ON DELETE CASCADE;


--
-- Name: form_shared form_shared_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.form_shared
    ADD CONSTRAINT form_shared_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.form(id) ON DELETE CASCADE;


--
-- Name: responses responses_field_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_field_id_fkey FOREIGN KEY (field_id) REFERENCES public.form_field(id) ON DELETE SET NULL;


--
-- Name: responses responses_response_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_response_id_fkey FOREIGN KEY (response_id) REFERENCES public.form_response(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 1lgLAP7AhZNCpETgNewZpgl00BSCIXO7dC6oR8EgdnbndDggYzuuOgmpBlFD7VH

