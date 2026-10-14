# TODO: fazer uma verificacao de qual banco de dados esta sendo utilizado

from .postgresql.index import db as __db

db = __db()
