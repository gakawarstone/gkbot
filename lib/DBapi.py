import psycopg2
from psycopg2.errors import UndefinedTable
from typing import Iterable, Optional, Any


class PostgreSQL:
    def __init__(self, url: str):
        self.connection = psycopg2.connect(url)

    def find_by_id(self, table_name: str, id: Any):
        for row in self.get_table(table_name):
            if row[0] == id:
                return row

    def get_table(self, name: str) -> list:
        try:
            query = f'SELECT * FROM {name}'
            return self.__get(query)
        except UndefinedTable:
            raise ValueError(f'Table {name} is undefined')

    def update_value(self, table_name: str, pr_key: list, set_value=list):
        ''' 
        pr_key = [name: str, val: Any]
        set_val = [name: str, val: Any]
        '''
        query = f'UPDATE {table_name} '
        query += f'SET {set_value[0]} = ' + '%s '
        query += f'WHERE {pr_key[0]} = ' + '%s'
        args = [set_value[1], pr_key[1]]
        self.__post(query, args)

    def append(self, table_name: str, data: list[tuple]):
        ''' id of table you trying to insert should be serial constraint '''
        for row in data:
            if not row:
                continue
            query = f'INSERT INTO {table_name} VALUES'
            if type(row) == tuple:
                query += ' (DEFAULT' + (',%s' * (len(row) - 1)) + ')'
                args = row
            else:
                assert type(row) != Iterable
                query += ' (DEFAULT, %s)'
                args = [row]
            self.__post(query, args)

    def insert_in(self, table_name: str, data: list[tuple]):
        for row in data:
            if not row:
                continue
            query = f'INSERT INTO {table_name} VALUES'
            if type(row) == tuple:
                query += ' (%s' + (',%s' * (len(row) - 1)) + ')'
                args = list(row)
            else:
                assert type(row) != tuple
                query += ' (%s)'
                args = [row]
            self.__post(query, args)

    def delete_from(self, table_name: str, properties: dict[str, list]):
        for column_name in properties:
            query = ''
            column_values = properties[column_name]
            for value in column_values:
                query += f'DELETE FROM {table_name} WHERE {column_name}'
                if value or value == 0:
                    query += ' = %s;'
                else:
                    assert value == None
                    query += ' IS NULL'
                    column_values.remove(value)
            self.__post(query, args=column_values)

    def __get(self, sql_query: str, args: Optional[list] = None) -> list:
        with self.connection:
            with self.__get_cursor() as cursor:
                if args:
                    cursor.execute(sql_query, (*args,))
                else:
                    cursor.execute(sql_query)
                return list(cursor.fetchall())

    def __post(self, sql_query: str, args: list):
        with self.connection:
            with self.__get_cursor() as cursor:
                cursor.execute(sql_query, (*args,))

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
