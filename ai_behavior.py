import random
from llm_interface import call_llm_api
from utils import print_color

class AIBehaviorSystem:
    """AI角色自主行为决策系统"""
    
    def __init__(self):
        self.decision_cache = {}  # 缓存决策结果，减少API调用
    
    def should_create_post(self, agent, community, force=False):
        """决定AI是否应该创建帖子"""
        if force:
            return True
            
        # 检查是否已经有太多帖子
        agent_posts = community.get_all_posts(author_id=agent.agent_id)
        if len(agent_posts) > 10:
            # 如果已经有很多帖子，降低发帖概率
            if random.random() > 0.3:
                return False
        
        # 基于角色记忆和兴趣生成决策
        cache_key = f"post_decision_{agent.agent_id}_{len(agent.memories)}"
        if cache_key in self.decision_cache:
            return self.decision_cache[cache_key]
            
        prompt = self._generate_post_decision_prompt(agent, community)
        decision = self._make_llm_decision(agent, prompt)
        
        # 缓存决策结果
        self.decision_cache[cache_key] = decision
        return decision
    
    def should_comment_on_post(self, agent, post, community, force=False):
        """决定AI是否应该评论特定帖子"""
        if force:
            return True
            
        # 检查是否是自己的帖子
        if post["author_id"] == agent.agent_id:
            return random.random() < 0.1  # 很少评论自己的帖子
            
        # 检查是否已经评论过这个帖子
        comments = community.get_post_comments(post["post_id"])
        for comment in comments:
            if comment["author_id"] == agent.agent_id:
                return False  # 已经评论过，不再评论
        
        # 基于帖子内容和角色兴趣决定
        cache_key = f"comment_decision_{agent.agent_id}_{post['post_id']}"
        if cache_key in self.decision_cache:
            return self.decision_cache[cache_key]
            
        prompt = self._generate_comment_decision_prompt(agent, post)
        decision = self._make_llm_decision(agent, prompt)
        
        # 缓存决策结果
        self.decision_cache[cache_key] = decision
        return decision
    
    def _generate_post_decision_prompt(self, agent, community):
        """生成用于决定是否发帖的提示"""
        recent_posts = community.get_all_posts(limit=5)
        recent_posts_text = ""
        
        for post in recent_posts:
            recent_posts_text += f"- {post['author_name']}发布了: {post['content'][:100]}...\n"
        
        recent_memories = "\n".join([f"- {memory}" for memory in agent.memories[-5:]])
        
        prompt = f"""作为{agent.name}({agent.role})，你需要决定是否在社区发布一个新帖子。

社区最近的帖子:
{recent_posts_text}

你的兴趣领域: {', '.join(agent.topics_of_interest)}

你最近的记忆:
{recent_memories}

根据以上信息，你认为现在是否应该发布一个新帖子？只需回复"是"或"否"。"""
        
        return prompt
    
    def _generate_comment_decision_prompt(self, agent, post):
        """生成用于决定是否评论的提示"""
        prompt = f"""作为{agent.name}({agent.role})，你看到了以下帖子:

作者: {post['author_name']}
内容: {post['content']}

你的兴趣领域: {', '.join(agent.topics_of_interest)}

这个帖子是否与你的兴趣相关或者值得你评论？只需回复"是"或"否"。"""
        
        return prompt
    
    def _make_llm_decision(self, agent, prompt):
        """通过LLM做出决策"""
        messages = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = call_llm_api(messages)
            
            if response and response.choices and len(response.choices) > 0:
                decision_text = response.choices[0].message.content.strip().lower()
                
                # 解析决策
                if "是" in decision_text[:10]:
                    return True
                else:
                    return False
        except Exception as e:
            print_color(f"决策过程中出错: {e}", "red")
            
        # 默认行为
        return random.random() < 0.5
    
    def select_post_topic(self, agent):
        """为AI选择一个要发帖的话题"""
        # 从角色兴趣中随机选择
        base_topic = random.choice(agent.topics_of_interest)
        
        # 从最近记忆中尝试找到相关主题
        relevant_memories = []
        for memory in agent.memories[-10:]:
            if any(topic.lower() in memory.lower() for topic in agent.topics_of_interest):
                relevant_memories.append(memory)
        
        if relevant_memories and random.random() < 0.7:
            # 70%几率使用最近相关记忆作为灵感
            inspiration = random.choice(relevant_memories)
            return f"关于{base_topic}的帖子，受到你这个记忆的启发: '{inspiration}'"
        
        return f"关于{base_topic}的帖子，展示你的专业知识和见解"
    
    def clear_cache(self):
        """清除决策缓存"""
        self.decision_cache.clear()