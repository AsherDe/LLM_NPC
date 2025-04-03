import json
import os
from datetime import datetime

class MemorySystem:
    def __init__(self, storage_dir="memories"):
        self.storage_dir = storage_dir
        
        # 如果存储目录不存在，则创建
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
    
    def save_agent_memories(self, agent_id, memories):
        """将角色的记忆保存到磁盘"""
        filename = os.path.join(self.storage_dir, f"{agent_id}_memories.json")
        
        data = {
            "agent_id": agent_id,
            "last_updated": datetime.now().isoformat(),
            "memories": memories
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_agent_memories(self, agent_id):
        """从磁盘加载角色的记忆"""
        filename = os.path.join(self.storage_dir, f"{agent_id}_memories.json")
        
        if not os.path.exists(filename):
            return []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("memories", [])
        except Exception as e:
            print(f"加载角色{agent_id}的记忆时出错: {e}")
            return []
    
    def save_agent_state(self, agent):
        """保存角色的完整状态，包括记忆、帖子、评论等"""
        filename = os.path.join(self.storage_dir, f"{agent.agent_id}_state.json")
        
        data = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "last_updated": datetime.now().isoformat(),
            "memories": agent.memories,
            "all_memories": agent.all_memories,
            "posts": agent.posts,
            "comments": agent.comments,
            "inspirations": agent.inspirations,
            "active_hours": agent.active_hours,
            "sleep_start": agent.sleep_start,
            "sleep_end": agent.sleep_end
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_agent_state(self, agent_id):
        """从磁盘加载角色的完整状态"""
        filename = os.path.join(self.storage_dir, f"{agent_id}_state.json")
        
        if not os.path.exists(filename):
            return None
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载角色{agent_id}的状态时出错: {e}")
            return None