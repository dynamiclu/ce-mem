"""
Dify Workflow Memory Plugin Provider
实现 manifest.yaml 中定义的 tool
"""

import json
from typing import Any, Callable, Dict, List

from diffeo_sdk import DiffeoClient

from ..memory_store import store, query, clear, get_info


class CEMemoryProvider:
    """CE Memory 插件提供者"""

    def __init__(self):
        self.name = "CEMemory"
        self.description = "Store and query multi-turn conversation memory"

    @staticmethod
    def credentials_for_provider() -> List[Dict[str, Any]]:
        """
        返回需要的凭据字段定义
        本插件为本地存储，不需要外部 API Key
        """
        return []

    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        验证凭据是否有效
        本插件不需要凭据，直接通过
        """
        pass

    def register(self, client: DiffeoClient):
        """注册工具到 Dify 客户端"""

        @client.tool(name="StoreMemory")
        def store_memory(
            key: str,
            role: str,
            content: str
        ) -> str:
            """
            Store a conversation turn into memory.

            Args:
                key: Unique identifier for the conversation session
                role: Message role, either "user" or "assistant"
                content: The message content

            Returns:
                JSON string with success status
            """
            try:
                success = store(key, role, content)
                return json.dumps({
                    "success": success,
                    "message": "Stored successfully" if success else "Store failed"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False)

        @client.tool(name="QueryMemory")
        def query_memory(
            key: str,
            size: int = 10
        ) -> str:
            """
            Query conversation memory.

            Args:
                key: Unique identifier for the conversation session
                size: Number of turns to retrieve (default: 10)

            Returns:
                JSON array string of conversation turns, ordered by time descending
            """
            try:
                if size <= 0:
                    size = 10
                return query(key, size)
            except Exception as e:
                return json.dumps([], ensure_ascii=False)

        @client.tool(name="ClearMemory")
        def clear_memory(key: str) -> str:
            """
            Clear all memory for a specific key.

            Args:
                key: Unique identifier for the conversation session

            Returns:
                JSON string with success status
            """
            try:
                success = clear(key)
                return json.dumps({
                    "success": success,
                    "message": "Cleared successfully" if success else "Clear failed"
                }, ensure_ascii=False)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "message": f"Error: {str(e)}"
                }, ensure_ascii=False)

        @client.tool(name="GetMemoryInfo")
        def get_memory_info(key: str) -> str:
            """
            Get memory metadata.

            Args:
                key: Unique identifier for the conversation session

            Returns:
                JSON object with memory metadata
            """
            try:
                info = get_info(key)
                return json.dumps(info, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": str(e)}, ensure_ascii=False)


def get_provider() -> CEMemoryProvider:
    """获取插件提供者实例"""
    return CEMemoryProvider()