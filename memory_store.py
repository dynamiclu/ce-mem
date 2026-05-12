"""
Dify Workflow Memory Plugin
解决工作流多次执行时的上下文记忆问题

存储结构:
- 内存缓存: LRUCache 加速读取
- 磁盘存储: 每个key一个JSON文件
- 时间倒序: 最新对话在前
- 自动压缩: 超过MAX_TURNS(100)条时合并旧记忆

Author: ce-mem
"""

import os
import json
import time
import threading
import hashlib
from collections import OrderedDict
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


# ========== 配置 ==========
BASE_DIR = Path(__file__).parent / "memory_data"
MAX_TURNS = 100          # 单key最大对话轮数
CACHE_MAX_SIZE = 500     # 缓存条目上限
CACHE_TTL = 60           # 缓存过期秒数
COMPRESS_THRESHOLD = 80  # 触发压缩的条数


# ========== 数据结构 ==========
@dataclass
class ConversationTurn:
    """单轮对话"""
    role: str          # "user" 或 "assistant"
    content: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryFile:
    """记忆文件结构"""
    key: str
    turns: List[ConversationTurn]
    version: int = 1
    created_at: float = 0
    updated_at: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turns": [t.to_dict() if isinstance(t, ConversationTurn) else t for t in self.turns]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryFile":
        turns = [ConversationTurn(**t) if isinstance(t, dict) else t for t in data.get("turns", [])]
        return cls(
            key=data["key"],
            turns=turns,
            version=data.get("version", 1),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0)
        )


# ========== LRU缓存 ==========
class LRUCache:
    """线程安全的LRU缓存"""

    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: int = CACHE_TTL):
        self._cache: OrderedDict[str, Tuple[float, List[Dict]]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[List[Dict]]:
        with self._lock:
            if key not in self._cache:
                return None
            ts, data = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return data

    def set(self, key: str, data: List[Dict]) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (time.time(), data)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


# ========== 全局实例 ==========
_cache = LRUCache()
_file_lock = threading.RLock()


# ========== 核心函数 ==========

def _get_file_path(key: str) -> Path:
    """根据key生成文件路径"""
    key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
    return BASE_DIR / f"{key_hash}.json"


def _ensure_base_dir():
    """确保存储目录存在"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def _load_from_file(key: str) -> Optional[MemoryFile]:
    """从文件加载记忆"""
    filepath = _get_file_path(key)
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return MemoryFile.from_dict(data)
    except (json.JSONDecodeError, KeyError, IOError):
        return None


def _save_to_file(memory: MemoryFile) -> None:
    """保存记忆到文件"""
    _ensure_base_dir()
    filepath = _get_file_path(memory.key)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(memory.to_dict(), f, ensure_ascii=False, indent=2)


def _compress_turns(turns: List[ConversationTurn]) -> List[ConversationTurn]:
    """压缩旧记忆：合并早期对话为摘要"""
    if len(turns) <= COMPRESS_THRESHOLD:
        return turns

    # 保留最近COMPRESS_THRESHOLD条，之前的合并为一条摘要
    recent = turns[:COMPRESS_THRESHOLD]
    old = turns[COMPRESS_THRESHOLD:]

    if not old:
        return recent

    # 生成摘要
    summary_parts = []
    for turn in old:
        role = "用户" if turn.role == "user" else "助手"
        content = turn.content[:50] + "..." if len(turn.content) > 50 else turn.content
        summary_parts.append(f"[{role}]: {content}")

    summary = ConversationTurn(
        role="system",
        content=f"[早期对话摘要，共{len(old)}轮]: " + " | ".join(summary_parts),
        timestamp=old[0].timestamp
    )

    return [summary] + recent


def _merge_turns(existing: List[ConversationTurn], new: ConversationTurn) -> List[ConversationTurn]:
    """合并新旧对话"""
    turns = [new] + existing  # 新对话在前（倒序）
    if len(turns) > MAX_TURNS:
        turns = _compress_turns(turns)
    return turns


# ========== 对外API ==========

def store(key: str, role: str, content: str) -> bool:
    """
    存储对话记忆

    Args:
        key: 唯一标识
        role: "user" 或 "assistant"
        content: 对话内容

    Returns:
        bool: 存储是否成功
    """
    try:
        with _file_lock:
            memory = _load_from_file(key)
            now = time.time()

            new_turn = ConversationTurn(role=role, content=content, timestamp=now)

            if memory is None:
                memory = MemoryFile(
                    key=key,
                    turns=[new_turn],
                    created_at=now,
                    updated_at=now
                )
            else:
                memory.turns = _merge_turns(memory.turns, new_turn)
                memory.updated_at = now

            _save_to_file(memory)
            _cache.invalidate(key)

            return True
    except Exception:
        return False


def query(key: str, size: int = 10) -> str:
    """
    查询对话记忆

    Args:
        key: 唯一标识
        size: 返回的对话轮数（每轮包含user+assistant）

    Returns:
        str: JSON字符串，包含对话对象列表，按时间倒序
    """
    # 优先从缓存获取
    cached = _cache.get(key)
    if cached is not None:
        result = cached[:size * 2] if len(cached) > size * 2 else cached
        return json.dumps(result, ensure_ascii=False)

    # 从文件加载
    memory = _load_from_file(key)
    if memory is None:
        return json.dumps([], ensure_ascii=False)

    # 转换为字典列表
    turns_data = [t.to_dict() if isinstance(t, ConversationTurn) else t for t in memory.turns]

    # 缓存结果
    _cache.set(key, turns_data)

    # 返回指定数量（按时间倒序）
    result = turns_data[:size * 2] if len(turns_data) > size * 2 else turns_data
    return json.dumps(result, ensure_ascii=False)


def clear(key: str) -> bool:
    """
    清除指定key的记忆

    Args:
        key: 唯一标识

    Returns:
        bool: 清除是否成功
    """
    try:
        with _file_lock:
            filepath = _get_file_path(key)
            if filepath.exists():
                filepath.unlink()
            _cache.invalidate(key)
            return True
    except Exception:
        return False


def get_info(key: str) -> Dict[str, Any]:
    """
    获取记忆信息（调试用）

    Returns:
        Dict: 包含条数、创建时间、更新等信息
    """
    memory = _load_from_file(key)
    if memory is None:
        return {"exists": False, "turns": 0}

    return {
        "exists": True,
        "turns": len(memory.turns),
        "version": memory.version,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at
    }


def main(action: str, key: str, content: str = "", role: str = "user", size: int = 10) -> dict:
    """
    Dify Code Node 入口
    参数:
        action: store/query/clear/info
        key: 唯一标识
        content: 存储内容
        role: user/assistant
        size: 查询条数
    返回:
        dict: 操作结果
    """
    if not key:
        return {"error": "key is required"}

    if action == "store":
        ok = store(key, role, content)
        return {"success": ok}
    elif action == "query":
        return {"result": query(key, size)}
    elif action == "clear":
        ok = clear(key)
        return {"success": ok}
    elif action == "info":
        return get_info(key)
    else:
        return {"error": f"Unknown action: {action}"}
