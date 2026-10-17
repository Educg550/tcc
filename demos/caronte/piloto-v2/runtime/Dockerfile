# Imagem do prejanus-back original (46b89c1, id sha256:0105d76c...) sem o código do produto:
# mesmas dependências exatas, inclusive o senhaunicapy vindo de git.
FROM caronte-core-prejanus-back:latest
USER root
RUN rm -rf src alembic.ini docker README.md pyproject.toml poetry.lock requirements.txt \
    && venv/bin/pip install --no-cache-dir --disable-pip-version-check pytest==9.0.3
USER appuser
