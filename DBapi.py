import psycopg2
import os

# Heroku PostgreSQL server
DATABASE_URL = os.environ.get('DATABASE_URL')


class PostgreSQL(object):
    def __init__(self, url):
        self.connection = psycopg2.connect(url)
        self.cursor = self.connection.cursor()

    def execute(self, sql_query):
        with self.cursor as cursor:
            cursor.execute(sql_query)
            return list(cursor.fetchall())


class Local(PostgreSQL):
    def __init__(self, dbname, user, password, host='5432'):
        self.connection = psycopg2.connect(dbname=dbname,
                                           user=user,
                                           password=password,
                                           host=host)
        self.cursor = self.connection.cursor()
