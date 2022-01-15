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


def test_insert_delete_values():
    db = connect_db()
    table_name = 'test'
    data = [(0, 1)]
    db.delete_from(table_name, {'number': data[0][0]})
    db.insert_in(table_name, data)
    db_after = connect_db()
    assert db_after.get_table(table_name) == [(0, 1)]
    db_after.delete_from(table_name, {'number': data[0][0]})


def test_insert_empty_list_in_table():
    db = connect_db()
    with pytest.raises(ValueError):
        # add_row functhion
        db.insert_in('test', [()])


# think how to do this test (add delete_row method)
def test_if_values_saving():
    db = connect_db()
    db.insert_in(value)
    db_new_connect = connect_db()
    assert db_new_connect.get_table('name') == [(value)]
    db_new_connect.remove_if_exist(value)
