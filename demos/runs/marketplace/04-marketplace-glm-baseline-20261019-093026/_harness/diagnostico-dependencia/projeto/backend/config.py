import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://marketplace:marketplace@127.0.0.1:55432/marketplace",
)
