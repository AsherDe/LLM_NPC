import datetime
import json
import os

def format_timestamp(timestamp_str):
    """将ISO格式的时间戳格式化为可读形式"""
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def summarize_text(text, max_length=100):
    """将文本截断为指定长度，添加省略号"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def log_to_file(message, log_file="system_log.txt"):
    """将消息记录到日志文件"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def ensure_directory(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_json(data, filename):
    """将数据保存为JSON文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename):
    """从JSON文件加载数据"""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件{filename}出错: {e}")
        return None

def count_tokens_estimate(text):
    """
    估计文本中的token数量
    这是一个粗略估计，仅用于内存管理
    中文每字约1-1.5个token，英文每4个字符约1个token
    """
    # 简单估计：中文字符计为1.5个token，其他字符4个计为1个token
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    
    return int(chinese_chars * 1.5 + other_chars / 4)

def print_color(text, color=None):
    """使用ANSI转义序列打印彩色文本"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        None: "\033[0m"
    }
    
    color_code = colors.get(color, colors[None])
    reset_code = colors[None]
    
    print(f"{color_code}{text}{reset_code}")

def get_current_time_str():
    """获取当前时间的字符串表示"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")