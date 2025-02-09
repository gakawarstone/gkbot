import pytest
import os
import uuid
from unittest.mock import patch

from workers.yt_dlp import Task


@pytest.fixture
def temp_cache_dir(tmpdir, monkeypatch):
    """Fixture to create a temporary cache directory and update Task paths."""
    temp_dir = str(tmpdir)
    # Mock the CACHE_DIR_PATH in the original module
    monkeypatch.setattr("workers.yt_dlp.CACHE_DIR_PATH", temp_dir)
    # Update the Task class variables to use the temp directory
    Task._tasks_file_path = os.path.join(temp_dir, "tasks")
    return temp_dir


def test_task_initialization(temp_cache_dir):
    """Test that a Task initializes correctly and creates its directory."""
    url = "http://example.com"
    task = Task(url)

    # Check URL and ID
    assert task.url == url
    assert isinstance(task.id, str)
    uuid.UUID(task.id)  # Raises ValueError if ID is not a UUID

    # Check directory creation
    expected_dir = os.path.join(temp_cache_dir, task.id)
    assert os.path.isdir(expected_dir)

    # Test directory conflict with the same UUID
    with patch("workers.yt_dlp.uuid4") as mock_uuid:
        mock_uuid.return_value = uuid.UUID(task.id)
        with pytest.raises(FileExistsError):
            Task(url)


def test_create_entry(temp_cache_dir):
    """Test that create_entry adds the task to the tasks file."""
    url = "http://example.com"
    task = Task(url)
    task.create_entry()

    # Check tasks file content
    with open(Task._tasks_file_path, "r") as f:
        lines = f.readlines()
    expected_entry = f"{url},{task.id}\n"
    assert expected_entry in lines


def test_delete_entry(temp_cache_dir):
    """Test that delete_entry removes the task from the tasks file."""
    task1 = Task("http://example.com")
    task1.create_entry()
    task2 = Task("http://another.com")
    task2.create_entry()

    # Delete task1's entry
    task1.delete_entry()

    # Verify remaining entries
    with open(Task._tasks_file_path, "r") as f:
        lines = f.readlines()
    assert f"{task1.url},{task1.id}\n" not in lines
    assert f"{task2.url},{task2.id}\n" in lines


def test_delete_entry_nonexistent_file(temp_cache_dir):
    """Test delete_entry when the tasks file doesn't exist."""
    task = Task("http://example.com")
    with pytest.raises(FileNotFoundError):
        task.delete_entry()


def test_check_video_exists(temp_cache_dir):
    """Test check_video_exists correctly identifies video presence."""
    task = Task("http://example.com")
    video_path = os.path.join(task.path, "video.webm")

    # Video does not exist initially
    assert not task.check_video_exists()

    # Create video and check existence
    open(video_path, "a").close()
    assert task.check_video_exists()

    # Remove video and check again
    os.remove(video_path)
    assert not task.check_video_exists()
