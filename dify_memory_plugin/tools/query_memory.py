"""QueryMemory Tool"""

import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from memory import query


class QueryMemoryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        key = tool_parameters.get("key")
        size = tool_parameters.get("size", 10)

        if not key:
            yield self.create_text_message("Missing required parameter: key")
            return

        result = query(key, size)
        data = json.loads(result)
        yield self.create_json_message(data)
