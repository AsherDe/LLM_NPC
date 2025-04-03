import json
import os
import datetime

class InteractionTracker:
    """跟踪AI角色之间的交互情况"""
    
    def __init__(self, storage_dir="interaction_data"):
        self.storage_dir = storage_dir
        self.interactions = {}  # {agent_id: {other_agent_id: 交互次数}}
        self.last_interaction = {}  # {agent_id: {other_agent_id: 最后交互时间}}
        
        # 确保存储目录存在
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        # 加载现有数据
        self.load_data()
    
    def record_interaction(self, agent1_id, agent2_id, interaction_type, details=None):
        """
        记录两个角色之间的交互
        
        参数:
            agent1_id: 发起交互的角色ID
            agent2_id: 接收交互的角色ID
            interaction_type: 交互类型 (如 'comment', 'like', 'reply')
            details: 可选的交互详情 (如帖子ID、评论内容等)
        """
        # 确保角色存在于交互记录中
        if agent1_id not in self.interactions:
            self.interactions[agent1_id] = {}
        if agent2_id not in self.interactions[agent1_id]:
            self.interactions[agent1_id][agent2_id] = 0
            
        # 增加交互计数
        self.interactions[agent1_id][agent2_id] += 1
        
        # 更新最后交互时间
        if agent1_id not in self.last_interaction:
            self.last_interaction[agent1_id] = {}
        self.last_interaction[agent1_id][agent2_id] = datetime.datetime.now().isoformat()
        
        # 记录详细的交互日志
        self._log_interaction(agent1_id, agent2_id, interaction_type, details)
        
        # 保存数据
        self.save_data()
    
    def _log_interaction(self, agent1_id, agent2_id, interaction_type, details):
        """记录详细的交互信息到日志文件"""
        log_file = os.path.join(self.storage_dir, "interaction_log.jsonl")
        
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent1_id": agent1_id,
            "agent2_id": agent2_id,
            "type": interaction_type,
            "details": details
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_interaction_count(self, agent1_id, agent2_id):
        """获取两个角色之间的交互次数"""
        if agent1_id not in self.interactions or agent2_id not in self.interactions[agent1_id]:
            return 0
        return self.interactions[agent1_id][agent2_id]
    
    def get_last_interaction_time(self, agent1_id, agent2_id):
        """获取两个角色最后交互的时间"""
        if agent1_id not in self.last_interaction or agent2_id not in self.last_interaction[agent1_id]:
            return None
        return self.last_interaction[agent1_id][agent2_id]
    
    def get_most_interacted(self, agent_id, limit=3):
        """获取与指定角色交互最多的前N个角色"""
        if agent_id not in self.interactions:
            return []
            
        # 按交互次数排序
        sorted_interactions = sorted(
            self.interactions[agent_id].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 返回前N个
        return sorted_interactions[:limit]
    
    def get_interaction_summary(self, agent_id):
        """获取角色的交互摘要"""
        if agent_id not in self.interactions:
            return {"total_interactions": 0, "unique_agents": 0}
            
        total = sum(self.interactions[agent_id].values())
        unique = len(self.interactions[agent_id])
        
        return {
            "total_interactions": total,
            "unique_agents": unique,
            "most_interacted": self.get_most_interacted(agent_id)
        }
    
    def save_data(self):
        """将交互数据保存到磁盘"""
        data = {
            "interactions": self.interactions,
            "last_interaction": self.last_interaction
        }
        
        filename = os.path.join(self.storage_dir, "interaction_data.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """从磁盘加载交互数据"""
        filename = os.path.join(self.storage_dir, "interaction_data.json")
        
        if not os.path.exists(filename):
            return
        
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.interactions = data.get("interactions", {})
                self.last_interaction = data.get("last_interaction", {})
        except Exception as e:
            print(f"加载交互数据时出错: {e}")