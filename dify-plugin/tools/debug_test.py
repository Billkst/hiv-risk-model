from collections.abc import Generator
from typing import Any
import logging
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.config.logger_format import plugin_logger_handler

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)


class DebugTestTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """简单的测试工具"""
        try:
            logger.info("=== Debug Test Tool Started ===")
            logger.info(f"Received parameters: {tool_parameters}")
            logger.info(f"Parameter keys: {list(tool_parameters.keys())}")
            logger.info(f"Parameter count: {len(tool_parameters)}")
            
            # 尝试多种方式获取输入
            test_input = None
            
            # 方式1: 标准方式
            if "test_input" in tool_parameters:
                test_input = tool_parameters["test_input"]
                logger.info(f"Got test_input via standard key: '{test_input}'")
            
            # 方式2: 尝试所有可能的key
            if not test_input:
                for key in tool_parameters.keys():
                    logger.info(f"Checking key: {key}, value: {tool_parameters[key]}")
                    if key.lower() in ["test_input", "testinput", "input", "text"]:
                        test_input = tool_parameters[key]
                        logger.info(f"Got test_input via alternate key '{key}': '{test_input}'")
                        break
            
            # 方式3: 如果只有一个参数，直接使用
            if not test_input and len(tool_parameters) == 1:
                test_input = list(tool_parameters.values())[0]
                logger.info(f"Got test_input as only parameter: '{test_input}'")
            
            # 方式4: 使用.get()兜底
            if not test_input:
                test_input = tool_parameters.get("test_input", "")
                logger.info(f"Got test_input via .get(): '{test_input}'")
            
            logger.info(f"Final test input value: '{test_input}'")
            logger.info(f"Final test input type: {type(test_input)}")
            
            # 如果仍然为空，返回诊断信息
            if not test_input:
                logger.warning("Test input is empty after all attempts")
                diagnostic_msg = (
                    f"⚠️ Debug Test Tool Diagnostic:\n"
                    f"- Received {len(tool_parameters)} parameters\n"
                    f"- Parameter keys: {list(tool_parameters.keys())}\n"
                    f"- Parameter values: {list(tool_parameters.values())}\n"
                    f"- No valid test_input found\n"
                    f"- Plugin is loaded and working, but parameter passing may have issues"
                )
                yield self.create_text_message(diagnostic_msg)
                yield self.create_json_message({
                    "status": "warning",
                    "message": "No input received",
                    "parameters_received": tool_parameters
                })
                return
            
            # 构建响应
            response_text = f"✅ Plugin is working! You said: {test_input}"
            logger.info(f"Sending response: {response_text}")
            
            # 返回文本消息
            yield self.create_text_message(response_text)
            
            # 返回JSON消息
            json_response = {
                "status": "success",
                "input": test_input,
                "message": "Debug test completed successfully",
                "parameters_received": list(tool_parameters.keys())
            }
            logger.info(f"Sending JSON: {json_response}")
            yield self.create_json_message(json_response)
            
            logger.info("=== Debug Test Tool Completed ===")
            
        except Exception as e:
            logger.error(f"Error in debug test: {str(e)}", exc_info=True)
            error_msg = (
                f"❌ Error in debug test: {str(e)}\n"
                f"Parameters received: {tool_parameters}"
            )
            yield self.create_text_message(error_msg)
            yield self.create_json_message({
                "status": "error",
                "error": str(e),
                "parameters": tool_parameters
            })
