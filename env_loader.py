import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 获取API密钥
def get_api_key():
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        raise ValueError("API密钥未设置。请在.env文件中设置ZHIPU_API_KEY。")
    return api_key

# 获取系统配置
def get_system_config():
    config = {
        "MEMORY_MAX_LENGTH": int(os.getenv("MEMORY_MAX_LENGTH", "10000")),
        "DEFAULT_SLEEP_START": int(os.getenv("DEFAULT_SLEEP_START", "1")),
        "DEFAULT_SLEEP_END": int(os.getenv("DEFAULT_SLEEP_END", "7")),
        "NIGHT_OWL_SLEEP_START": int(os.getenv("NIGHT_OWL_SLEEP_START", "2")),
        "NIGHT_OWL_SLEEP_END": int(os.getenv("NIGHT_OWL_SLEEP_END", "9")),
        "ACTIVE_HOURS_MIN": int(os.getenv("ACTIVE_HOURS_MIN", "3")),
        "ACTIVE_HOURS_MAX": int(os.getenv("ACTIVE_HOURS_MAX", "8")),
    }
    return config

# 获取数据存储路径
def get_storage_dirs():
    dirs = {
        "MEMORY_STORAGE_DIR": os.getenv("MEMORY_STORAGE_DIR", "memories"),
        "COMMUNITY_STORAGE_DIR": os.getenv("COMMUNITY_STORAGE_DIR", "community_data"),
    }
    return dirs