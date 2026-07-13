"""
Dify Workflow Memory Plugin - 核心存储引擎
解决工作流多次执行时的上下文记忆问题
"""

import os
import json
import time
import threading
import hashlib
from collections import OrderedDict
from pathlib import Path
from typing import Optional

# ========== 配置 ==========
BASE_DIR = Path(__file__).parent / "memory_data"
MAX_TURNS = 100
CACHE_MAX_SIZE = 500
CACHE_TTL = 60

# ========== LRU 缓存 ==========
class LRUCache:
    """线程安全的 LRU 缓存"""

    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: int = CACHE_TTL):
        self._cache: OrderedDict[str, tuple[float, list[dict]]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[list[dict]]:
        with self._lock:
            if key not in self._cache:
                return None
            ts, data = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return data

    def set(self, key: str, data: list[dict]) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (time.time(), data)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)


_cache = LRUCache()
_file_lock = threading.RLock()


# ========== 工具函数 ==========

def _get_file_path(key: str) -> Path:
    key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
    return BASE_DIR / f"{key_hash}.json"


def _ensure_dir():
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def _load(key: str) -> Optional[dict]:
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


def _compress(turns: list[dict], threshold: int = 80) -> list[dict]:
    """超过阈值时压缩旧记忆为摘要"""
    if len(turns) <= threshold:
        return turns

    recent = turns[:threshold]
    old = turns[threshold:]

    summary = {
        "role": "system",
        "content": f"[早期对话摘要，共 {len(old)} 轮]: " + " | ".join(
            f"[{'用户' if t['role'] == 'user' else '助手'}]: {t['content'][:50]}{'...' if len(t['content']) > 50 else ''}"
            for t in old
        ),
        "timestamp": old[0]["timestamp"]
    }
    return [summary] + recent


# ========== 核心 API ==========

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
                    data["turns"] = _compress(data["turns"])
                data["updated_at"] = now

            _save(key, data)
            _cache.invalidate(key)
            return True
    except Exception:
        return False


def query(key: str, size: int = 10) -> str:
    """查询对话记忆（时间倒序）"""
    cached = _cache.get(key)
    if cached is not None:
        result = cached[:size * 2]
        return json.dumps(result, ensure_ascii=False)

    data = _load(key)
    if data is None:
        return json.dumps([], ensure_ascii=False)

    turns = data["turns"]
    _cache.set(key, turns)

    result = turns[:size * 2]
    return json.dumps(result, ensure_ascii=False)


def clear(key: str) -> bool:
    """清除指定 key 的记忆"""
    try:
        with _file_lock:
            filepath = _get_file_path(key)
            if filepath.exists():
                filepath.unlink()
            _cache.invalidate(key)
            return True
    except Exception:
        return False


def get_info(key: str) -> dict:
    """获取记忆元信息"""
    data = _load(key)
    if data is None:
        return {"exists": False, "turns": 0}
    return {
        "exists": True,
        "turns": len(data["turns"]),
        "created_at": data.get("created_at", 0),
        "updated_at": data.get("updated_at", 0)
    }
