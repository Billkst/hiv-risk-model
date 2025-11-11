from collections.abc import Generator
from typing import Any
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class DebugTestSimpleTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """最简单的测试工具 - 无日志，无复杂逻辑"""
        # 直接返回固定消息，不依赖任何参数
        yield self.create_text_message("Plugin loaded successfully!")
