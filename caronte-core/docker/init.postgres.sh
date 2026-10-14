#!/bin/bash
set -e

S1_DB=${FORMS_DB:-sistema1_db}
S1_USER=${FORMS_USER:-sistema1_user}
S1_PASS=${FORMS_PASSWORD:-senha1}

S2_DB=${PREJANUS_DB:-sistema2_db}
S2_USER=${PREJANUS_USER:-sistema2_user}
S2_PASS=${PREJANUS_PASSWORD:-senha2}

S1_READER=${FORMS_READER:-sistema1_reader}
S1_READER_PASS=${FORMS_READER_PASSWORD:-senha_read}
export PGPASSWORD=${POSTGRES_ADMIN_PASSWORD}

echo "${S1_USER} and ${S2_USER} and ${S1_READER}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d postgres <<-EOSQL

create database ${S1_DB};
create database ${S2_DB};

create user ${S1_USER} with encrypted password '${S1_PASS}';
create user ${S2_USER} with encrypted password '${S2_PASS}';
create user ${S1_READER} with encrypted password '${S1_READER_PASS}';

grant all privileges on database ${S1_DB} to ${S1_USER};
grant all privileges on database ${S2_DB} to ${S2_USER};
grant connect on database ${S1_DB} to ${S1_READER};

\c ${S2_DB}

grant usage on schema public to ${S2_USER};
grant create on schema public to ${S2_USER};

alter default privileges in schema public
    grant all privileges on tables to ${S2_USER};

\c ${S1_DB}

grant usage on schema public to ${S1_READER};
grant insert, select, update on all tables in schema public to ${S1_READER};
grant usage, select on all sequences in schema public to ${S1_READER};
grant execute on all functions in schema public to ${S1_READER};

alter default privileges for role ${S1_USER} in schema public 
    grant insert, select, update on tables to ${S1_READER};

alter default privileges for role ${S1_USER} in schema public
    grant usage, select on sequences to ${S1_READER};

alter default privileges for role ${S1_USER} in schema public
    grant execute on functions to ${S1_READER};

create extension if not exists "unaccent";
select * FROM pg_extension;

grant usage on schema public to ${S1_USER};
grant create on schema public to ${S1_USER};

alter default privileges for role ${S1_USER} in schema public
    grant all privileges on tables to ${S1_USER};

EOSQL