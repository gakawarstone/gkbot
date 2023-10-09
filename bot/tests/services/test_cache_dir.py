import os

from services.cache_dir import CacheDir


def test_save_file():
    cache_dir = CacheDir()
    content = b"Hello, World!"
    file_name = "test_file.txt"

    cache_dir.save_file(file_name, content)
    file_path = cache_dir.get_file_path(file_name)

    assert os.path.exists(file_path)

    with open(file_path, "rb") as f:
        assert f.read() == content


def test_get_file_path():
    cache_dir = CacheDir()
    file_name = "test_file.txt"
    expected_path = os.path.join(cache_dir.path, file_name)

    assert cache_dir.get_file_path(file_name) == expected_path


def test_delete():
    cache_dir = CacheDir()
    cache_dir.delete()

    assert not os.path.exists(cache_dir.path)


def test_init_creates_directory():
    cache_dir = CacheDir()

    assert os.path.exists(cache_dir.path)


def test_init_creates_unique_directories():
    cache_dir_1 = CacheDir()
    cache_dir_2 = CacheDir()

    assert cache_dir_1.path != cache_dir_2.path
