"""ClearMemory Tool"""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from memory import clear


class ClearMemoryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        key = tool_parameters.get("key")

        if not key:
            yield self.create_text_message("Missing required parameter: key")
            return

        success = clear(key)
        yield self.create_json_message({"success": success, "message": "Cleared successfully" if success else "Clear failed"})
