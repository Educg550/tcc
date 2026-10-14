import psycopg
from contextlib import contextmanager

from app.logger import Logger

from app.persistence.migrate import migrate_runner

class db:
    def initialize(self, config):
        self.config = {
            "host": config['POSTGRES_HOST'],
            "dbname": config['POSTGRES_DB'],
            "user": config['POSTGRES_USER'],
            "password": config['POSTGRES_PASSWORD'],
            "port": config['POSTGRES_PORT']
        }

        try:
            migrate_runner(self)
        except (psycopg.DatabaseError, Exception) as error:
            Logger.print.error(error)
        else:
            Logger.print.info('Initialized to the PostgreSQL server.')
    
    @contextmanager
    def transaction(self):
        with psycopg.connect(**self.config) as conn:
            class commands:
                @staticmethod
                def sql(command, parameters = None, callback = None, conn = conn):
                    with conn.cursor() as cur:
                        if parameters is None:
                            cur.execute(command)
                        else:
                            cur.execute(command, parameters)
                        if callback is not None: 
                            return callback(cur)

                @staticmethod
                def sql_dict(command, parameters = None, callback = None, conn = conn):
                    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                        if parameters is None:
                            cur.execute(command)
                        else:
                            cur.execute(command, parameters)
                        if callback is not None: 
                            return callback(cur)

            
            try:
                yield commands
                conn.commit()
            except Exception as exception:
                Logger.print.warning(exception)
                conn.rollback()