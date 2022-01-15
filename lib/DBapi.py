import psycopg2
from psycopg2.errors import UndefinedTable
from typing import Optional, Union


class PostgreSQL:
    def __init__(self, url: str):
        self.connection = psycopg2.connect(url)

    def get_table(self, name: str) -> list:
        try:
            query = f'SELECT * FROM {name}'
            return self.__get(query)
        except UndefinedTable:
            raise ValueError(f'Table {name} is undefined')

    def insert_in(self, table_name: str, data: list[tuple]):
        for row in data:
            query = f'INSERT INTO {table_name} VALUES'
            query += ' (%s' + (',%s' * (len(row) - 1)) + ')'
            args = row
            self.__post(query, args)

    def delete_from(self, table_name: str, properties: dict):
        for column_name in properties:
            column_value = properties[column_name]
            query = f'DELETE FROM {table_name} WHERE  {column_name} ='
            query += ' %(value)s'
            self.__post(
                query, args={'value': column_value})

    def __get(self, sql_query: str, args: Optional[tuple] = None) -> list:
        with self.connection:
            with self.__get_cursor() as cursor:
                if args:
                    cursor.execute(sql_query, (*args,))
                else:
                    cursor.execute(sql_query)
                return list(cursor.fetchall())

    def __post(self, sql_query: str, args: Union[tuple, dict]):
        with self.connection:
            with self.__get_cursor() as cursor:
                if type(args) == tuple:
                    cursor.execute(sql_query, (*args,))
                elif type(args) == dict:
                    cursor.execute(sql_query, args)

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
