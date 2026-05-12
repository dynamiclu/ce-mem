"""
Dify CE Memory Plugin

使用方式:
    from dify_memory_plugin.memory_store import store, query
    from dify_memory_plugin.api import store_memory, query_memory

存储示例:
    store("session_123", "user", "你好")
    store("session_123", "assistant", "你好！有什么可以帮你的？")

查询示例:
    result = query("session_123", size=5)  # 返回最近5轮对话

Dify Workflow 调用:
    - 存储节点: 调用 store_memory(key, query_content, llm_response)
    - 查询节点: 调用 query_memory(key, size)
"""

from .memory_store import store, query, clear, get_info
from .api import store_memory, query_memory, clear_memory, get_memory_info

__all__ = [
    "store",
    "query",
    "clear",
    "get_info",
    "store_memory",
    "query_memory",
    "clear_memory",
    "get_memory_info",
]

__version__ = "1.0.0"
