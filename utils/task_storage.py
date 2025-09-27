"""Simple JSON-backed storage for per-user task lists."""
from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Dict, List

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "files" / "user_tasks.json"
_TASKS_FILE = Path(os.getenv("USER_TASKS_FILE", _DEFAULT_PATH))
_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)

_LOCK = Lock()


def _load_all() -> Dict[str, List[dict]]:
    if not _TASKS_FILE.exists():
        return {}
    try:
        with _TASKS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return {str(k): list(v) for k, v in data.items()}
    except json.JSONDecodeError:
        pass
    return {}


def _save_all(data: Dict[str, List[dict]]) -> None:
    tmp_path = _TASKS_FILE.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    tmp_path.replace(_TASKS_FILE)


def list_tasks(user_id: int) -> List[dict]:
    with _LOCK:
        data = _load_all()
        return list(data.get(str(user_id), []))


def add_task(user_id: int, text: str) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("Task text must not be empty.")

    with _LOCK:
        data = _load_all()
        user_key = str(user_id)
        user_tasks = list(data.get(user_key, []))
        next_id = (max((task.get("id", 0) for task in user_tasks), default=0) + 1)
        task = {"id": next_id, "text": text}
        user_tasks.append(task)
        data[user_key] = user_tasks
        _save_all(data)
        return task


def remove_task(user_id: int, task_id: int) -> bool:
    with _LOCK:
        data = _load_all()
        user_key = str(user_id)
        user_tasks = list(data.get(user_key, []))
        original_len = len(user_tasks)
        user_tasks = [task for task in user_tasks if task.get("id") != task_id]
        if len(user_tasks) == original_len:
            return False
        data[user_key] = user_tasks
        _save_all(data)
        return True


def clear_tasks(user_id: int) -> None:
    with _LOCK:
        data = _load_all()
        if str(user_id) in data:
            del data[str(user_id)]
            _save_all(data)
