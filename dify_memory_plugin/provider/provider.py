"""CEMemory Provider"""

from typing import Any

from dify_plugin import ToolProvider


class CEMemoryProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """验证凭据 - 本插件不需要凭据"""
        pass


def get_provider():
    return CEMemoryProvider()
