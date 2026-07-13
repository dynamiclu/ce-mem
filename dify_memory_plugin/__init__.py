"""
Dify CE Memory Plugin
用于 Dify Workflow 的多轮对话记忆插件
"""

from memory import store, query, clear, get_info
from .api import store_memory, query_memory, clear_memory, get_memory_info

__all__ = [
    "store", "query", "clear", "get_info",
    "store_memory", "query_memory", "clear_memory", "get_memory_info",
]

__version__ = "1.0.0"
