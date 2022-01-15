import pytest

from bot_config import LOCAL_DB_USER_PSWD
from lib.DBapi import Local


def connect_db():
    return Local(dbname='unit_test',
                 user=LOCAL_DB_USER_PSWD[0],
                 password=LOCAL_DB_USER_PSWD[1])


def test_init():
    connect_db()


def test_get_table():
    db = connect_db()
    assert db.get_table('test_get') == [(0, 'Hello')]


def test_if_table_not_exist():
    db = connect_db()
    with pytest.raises(ValueError):
        data = ['not_exist', 'try', '1111', 'FGHN']
        for tb in data:
            db.get_table(tb)


def test_insert_empty_list_in_table():
    db = connect_db()
    db.insert_in('test', [()])


def test_delete():
    db = connect_db()
    db.delete_from('test', {'number': [1]})


def test_insert_delete_values():
    for i in range(10):
        db = connect_db()
        table_name = 'test'
        data = [(0, i), (1, i), (2)]
        db.delete_from(table_name, {'number': [i, None]})
        db.insert_in(table_name, data)
        db_after = connect_db()
        data[2] = (2, None)
        assert db_after.get_table(table_name) == data
        db_after.delete_from(table_name, {'number': [i, None]})


def test_append():
    for i in range(10):
        db = connect_db()
        table_name = 'test'
        data = [(1), (2), (3)]
        db.append(table_name, data)
        assert [i[1] for i in db.get_table(table_name)] == data
        for e in data:
            db.delete_from(table_name, {'number': [e]})
