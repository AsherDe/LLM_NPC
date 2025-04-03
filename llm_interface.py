from zhipuai import ZhipuAI
from config import API_KEY
import os

# 初始化客户端
client = ZhipuAI(api_key="1ff92264a5ac41ac9579c1e2fa2ffc7a.Dv5xnTJuHLj4oYX8")

def call_llm_api(messages, tools=None):
    """
    调用智谱AI GLM-4 API.
    
    参数:
        messages (list): 包含'role'和'content'键的消息字典列表
        tools (list, optional): API的工具配置列表
        
    返回:
        API响应对象
    """
    try:
        # 从环境变量获取模型名称，默认为glm-4
        model_name = os.getenv("ZHIPU_MODEL_NAME", "glm-4-plus")
        
        if tools:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools
            )
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages
            )
        
        return response
    except Exception as e:
        print(f"调用LLM API时出错: {e}")
        return None