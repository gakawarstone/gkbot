import psycopg2


class PostgreSQL:
    def __init__(self, url: str):
        self.connection = psycopg2.connect(url)

    def __get_cursor(self):
        return self.connection.cursor()

    def get_table(self, name: str):
        return self.execute(f'SELECT * FROM {name}')

    def execute(self, sql_query: str):
        with self.__get_cursor() as cursor:
            cursor.execute(sql_query)
            return list(cursor.fetchall())


class Local(PostgreSQL):
    def __init__(self, dbname: str,
                 user: str,
                 password: str,
                 host: str = 'localhost'):
        self.connection = psycopg2.connect(dbname=dbname,
                                           user=user,
                                           password=password,
                                           host=host)
        self.cursor = self.connection.cursor()
