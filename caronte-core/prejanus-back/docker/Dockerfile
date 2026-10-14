FROM python:3.11-slim as requirements-stage

WORKDIR /tmp

RUN pip install poetry
RUN pip install poetry-plugin-export

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update; \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    git \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

ENV VIRTUAL_ENV=/home/appuser/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --chown=appuser:appuser --from=requirements-stage /tmp/requirements.txt /home/appuser/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /home/appuser/requirements.txt

COPY --chown=appuser:appuser . /home/appuser

CMD uvicorn src.main:app --host 0.0.0.0 --port 8000