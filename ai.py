# AI处理模块

import json
import re
import time
import sys
import os
from openai import OpenAI

# 从config.json读取debug配置
def load_debug_config():
    """从config.json加载debug配置"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('debug', False)
    except Exception:
        return False

DEBUG = load_debug_config()

def print_debug(message):
    """打印调试信息"""
    if DEBUG:
        print(f"[AI DEBUG] {message}")

class AI:
    """AI管理类"""

    def __init__(self, config):
        """初始化AI管理器"""
        # 保存配置
        self.api_key = config.get('api_key', '')
        self.api_base = config.get('api_base', 'https://api.openai.com/v1')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.system_prompt = config.get('system_prompt', '')
        self.functions_config = config.get('functions', [])

        # 动态导入functions模块
        self.functions_module = self.load_functions_module()

        # 初始化OpenAI客户端
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
            print_debug("OpenAI客户端初始化成功")
        except Exception as e:
            print_debug(f"OpenAI客户端初始化失败: {str(e)}")
            self.client = None

        # 消息历史记录
        self.messages = []

        # 添加系统提示词
        if self.system_prompt:
            self.messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # 准备工具描述
        self.tools = self.prepare_tools()

        print_debug(f"AI初始化完成，支持{len(self.tools)}个工具")

    def load_functions_module(self):
        """动态加载functions模块"""
        try:
            # 获取当前执行目录
            current_dir = os.getcwd()
            functions_path = os.path.join(current_dir, 'functions.py')

            print_debug(f"尝试加载functions模块: {functions_path}")

            if not os.path.exists(functions_path):
                print_debug("functions.py文件不存在，功能调用将不可用")
                return None

            # 动态导入functions模块
            import importlib.util
            spec = importlib.util.spec_from_file_location("functions", functions_path)
            functions_module = importlib.util.module_from_spec(spec)

            # 将模块添加到sys.modules中，避免重复加载
            sys.modules["functions"] = functions_module
            spec.loader.exec_module(functions_module)

            print_debug("functions模块加载成功")
            return functions_module

        except Exception as e:
            print_debug(f"加载functions模块失败: {str(e)}")
            return None

    def execute_function(self, function_name, arguments):
        """执行指定的函数"""
        if not self.functions_module:
            return f"错误：functions模块未加载，无法执行函数 '{function_name}'"

        try:
            # 检查functions模块是否有execute_function方法
            if hasattr(self.functions_module, 'execute_function'):
                return self.functions_module.execute_function(function_name, arguments)
            else:
                return f"错误：functions模块中没有execute_function方法"
        except Exception as e:
            print_debug(f"函数执行失败: {str(e)}")
            return f"错误：函数执行失败 - {str(e)}"

    def prepare_tools(self):
        """准备工具描述列表"""
        tools = []
        for func in self.functions_config:
            tool = {
                "type": "function",
                "function": {
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": func["parameters"]
                }
            }
            tools.append(tool)
        return tools
    
    def send_message(self, user_message):
        """发送消息给AI并获取回复"""
        if not self.client:
            return "错误：AI客户端未初始化，请检查API配置"
        
        try:
            # 添加用户消息到历史
            self.messages.append({
                "role": "user", 
                "content": user_message
            })
            print_debug(f"发送用户消息: {user_message}")
            # 准备API调用参数
            api_params = {
                "model": self.model,
                "messages": self.messages
            }
            # 如果有工具，添加到参数中
            if self.tools:
                api_params["tools"] = self.tools
            # 第一次API调用
            print_debug("正在调用AI API...")
            response = self.client.chat.completions.create(**api_params)
            ai_response = response.choices[0].message.content or ""
            print_debug(f"AI原始回复: {ai_response}")
            if self.get_message_count() >=5:
                print_debug("消息历史超过5条，清空历史")
                self.clear_history()
            # 将AI回复添加到消息历史
            self.messages.append({
                "role": "assistant",
                "content": ai_response
            })
            # 检查是否需要调用工具
            final_response = self.handle_function_calls(ai_response)
            return final_response
            
        except Exception as e:
            error_msg = f"AI处理失败: {str(e)}"
            print_debug(error_msg)
            return error_msg
    
    def handle_function_calls(self, ai_response):
        """处理AI回复中的函数调用"""
        # 查找JSON代码块
        json_match = re.search(r"```json\s*(.*?)\s*```", ai_response, re.DOTALL)
        
        if not json_match:
            # 没有函数调用，直接返回AI回复
            return ai_response
        
        try:
            # 解析JSON
            json_str = json_match.group(1)
            tool_data = json.loads(json_str)
            print_debug(f"发现函数调用: {tool_data}")
            # 检查是否有tool_calls
            if "tool_calls" not in tool_data or not tool_data["tool_calls"]:
                return ai_response
            # 处理每个工具调用
            for tool_call in tool_data["tool_calls"]:
                call_id = tool_call.get("id", "unknown")
                function_name = tool_call.get("function", {}).get("name", "")
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                
                print_debug(f"执行函数: {function_name}, 参数: {arguments_str}")
                # 解析函数参数
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    error_msg = f"函数参数解析失败: {arguments_str}"
                    print_debug(error_msg)
                    # 添加错误信息到消息历史
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": error_msg
                    })
                    continue
                # 执行函数
                result = self.execute_function(function_name, arguments)
                print_debug(f"函数执行结果: {result}")

                # 检查是否是图片分析结果
                if isinstance(result, dict) and result.get("type") == "image_for_ai":
                    # 这是图片数据，需要特殊处理
                    print_debug("检测到图片数据，准备发送给AI分析")

                    # 添加函数结果到消息历史（简化版本）
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result.get("message", "截图完成")
                    })

                    # 准备包含图片的用户消息
                    image_message = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": result.get("user_question", "请描述这张截图的内容")
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": result["data_url"]
                                }
                            }
                        ]
                    }

                    # 将图片消息添加到历史中
                    self.messages.append(image_message)
                    print_debug("已添加图片消息到对话历史")

                else:
                    # 普通函数结果，按原来的方式处理
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": str(result)
                    })
            
            # 第二次API调用，让AI根据函数结果给出最终回复
            print_debug("正在获取AI最终回复...")
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            
            final_ai_response = final_response.choices[0].message.content or ""
            print_debug(f"AI最终回复: {final_ai_response}")

            if self.get_message_count() >=5:
                print_debug("消息历史超过5条，清空历史")
                self.clear_history()
            # 添加最终回复到消息历史
            self.messages.append({
                "role": "assistant",
                "content": final_ai_response
            })
            
            return final_ai_response
            
        except json.JSONDecodeError as e:
            print_debug(f"JSON解析错误: {str(e)}")
            # JSON解析失败，返回原始回复
            return ai_response
        except Exception as e:
            error_msg = f"函数调用处理失败: {str(e)}"
            print_debug(error_msg)
            return f"{ai_response}\n\n{error_msg}"
    
    def get_message_count(self):
        """获取消息历史数量"""
        return len(self.messages)
    
    def clear_history(self):
        """清空消息历史（保留系统提示词）"""
        # 保留系统提示词
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_messages
        print_debug("消息历史已清空")

    def get_last_messages(self, count=5):
        """获取最近的几条消息"""
        return self.messages[-count:] if len(self.messages) >= count else self.messages
