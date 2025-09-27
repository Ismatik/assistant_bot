import importlib
import sys

import pytest


@pytest.fixture()
def task_storage_module(tmp_path, monkeypatch):
    storage_path = tmp_path / "tasks.json"
    monkeypatch.setenv("USER_TASKS_FILE", str(storage_path))
    if "assistant_bot.utils.task_storage" in sys.modules:
        del sys.modules["assistant_bot.utils.task_storage"]
    if "utils.task_storage" in sys.modules:
        del sys.modules["utils.task_storage"]
    module = importlib.import_module("assistant_bot.utils.task_storage")
    importlib.reload(module)
    return module


def test_add_and_list_tasks(task_storage_module):
    storage = task_storage_module

    assert storage.list_tasks(1) == []

    task = storage.add_task(1, "Write documentation")
    assert task["id"] == 1
    assert task["text"] == "Write documentation"

    second = storage.add_task(1, "Review pull request")
    assert second["id"] == 2

    tasks = storage.list_tasks(1)
    assert [t["text"] for t in tasks] == ["Write documentation", "Review pull request"]


def test_remove_and_clear_tasks(task_storage_module):
    storage = task_storage_module
    storage.add_task(5, "Task A")
    storage.add_task(5, "Task B")

    assert storage.remove_task(5, 1) is True
    assert [t["text"] for t in storage.list_tasks(5)] == ["Task B"]

    assert storage.remove_task(5, 999) is False

    storage.clear_tasks(5)
    assert storage.list_tasks(5) == []
