"""Memory storage module"""
import json
import time
import hashlib
from pathlib import Path
from collections import OrderedDict
import threading

MAX_TURNS = 100
BASE_DIR = Path(__file__).parent / "memory_data"

_cache: OrderedDict = OrderedDict()
_cache_lock = threading.Lock()
_file_lock = threading.RLock()


def _get_file_path(key: str) -> Path:
    key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
    return BASE_DIR / f"{key_hash}.json"


def _ensure_dir():
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def _load(key: str) -> dict:
    filepath = _get_file_path(key)
    if not filepath.exists():
        return None
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save(key: str, data: dict) -> None:
    _ensure_dir()
    filepath = _get_file_path(key)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def store(key: str, role: str, content: str) -> bool:
    """存储对话记忆"""
    try:
        with _file_lock:
            now = time.time()
            new_turn = {"role": role, "content": content, "timestamp": now}
            data = _load(key)
            if data is None:
                data = {"key": key, "turns": [new_turn], "created_at": now, "updated_at": now}
            else:
                data["turns"] = [new_turn] + data["turns"]
                if len(data["turns"]) > MAX_TURNS:
                    data["turns"] = data["turns"][:MAX_TURNS]
                data["updated_at"] = now
            _save(key, data)
            return True
    except Exception:
        return False


def query(key: str, size: int = 10) -> str:
    """查询对话记忆"""
    data = _load(key)
    if data is None:
        return "[]"
    turns = data["turns"]
    result = turns[:size * 2]
    return json.dumps(result, ensure_ascii=False)


def clear(key: str) -> bool:
    """清除记忆"""
    try:
        with _file_lock:
            filepath = _get_file_path(key)
            if filepath.exists():
                filepath.unlink()
            return True
    except Exception:
        return False


def get_info(key: str) -> dict:
    """获取记忆信息"""
    data = _load(key)
    if data is None:
        return {"exists": False, "turns": 0}
    return {
        "exists": True,
        "turns": len(data["turns"]),
        "created_at": data.get("created_at", 0),
        "updated_at": data.get("updated_at", 0)
    }
