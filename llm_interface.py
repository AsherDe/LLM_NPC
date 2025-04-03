from zhipuai import ZhipuAI
from config import API_KEY

# 初始化客户端
client = ZhipuAI(api_key=API_KEY)

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
        if tools:
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                tools=tools
            )
        else:
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages
            )
        
        return response
    except Exception as e:
        print(f"调用LLM API时出错: {e}")
        return None