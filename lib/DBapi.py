import psycopg2


class PostgreSQL:
    def __init__(self, url: str):
        self.connection = psycopg2.connect(url)

    def get_table(self, name: str) -> list:
        return self.__get(f'SELECT * FROM {name}')

    def insert_in(self, table_name: str, data: list[tuple]):
        for row in data:
            self.__post(f'INSERT INTO {table_name} VALUES {row}')

    def __get(self, sql_query: str) -> list:
        with self.__get_cursor() as cursor:
            cursor.execute(sql_query)
            return list(cursor.fetchall())

    def __post(self, sql_query: str):
        with self.__get_cursor() as cursor:
            cursor.execute(sql_query)

    def __get_cursor(self):
        return self.connection.cursor()


class Local(PostgreSQL):
    def __init__(self, dbname: str,
                 user: str,
                 password: str,
                 host: str = 'localhost'):
        self.connection = psycopg2.connect(dbname=dbname,
                                           user=user,
                                           password=password,
                                           host=host)
