"""StoreMemory Tool"""

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from memory import store


class StoreMemoryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        key = tool_parameters.get("key")
        role = tool_parameters.get("role")
        content = tool_parameters.get("content")

        if not all([key, role, content]):
            yield self.create_text_message("Missing required parameters: key, role, content")
            return

        success = store(key, role, content)
        yield self.create_json_message({"success": success, "message": "Stored successfully" if success else "Store failed"})
