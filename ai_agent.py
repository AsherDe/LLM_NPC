import random
import datetime
from config import ACTIVE_HOURS_MIN, ACTIVE_HOURS_MAX, DEFAULT_SLEEP_START, DEFAULT_SLEEP_END, NIGHT_OWL_SLEEP_START, NIGHT_OWL_SLEEP_END
from llm_interface import call_llm_api

class AIAgent:
    def __init__(self, agent_id, name, role, memories, behaviors, topics_of_interest, system_prompt, night_owl=False, speaking_style=None, background=None):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.memories = memories.copy()  # 初始记忆
        self.all_memories = memories.copy()  # 完整历史记忆
        self.behaviors = behaviors
        self.topics_of_interest = topics_of_interest
        self.system_prompt = system_prompt
        self.speaking_style = speaking_style or ""
        self.background = background or ""
        self.night_owl = night_owl
        
        # 测试模式设置
        self.force_active = False  # 是否强制角色始终保持活跃状态
        
        # 根据夜猫子状态设置睡眠时间
        if night_owl:
            self.sleep_start = NIGHT_OWL_SLEEP_START
            self.sleep_end = NIGHT_OWL_SLEEP_END
        else:
            self.sleep_start = DEFAULT_SLEEP_START
            self.sleep_end = DEFAULT_SLEEP_END
            
        # 生成今天的活跃时间（每天会重新生成）
        self.active_hours = self._generate_active_hours()
        
        # 跟踪帖子和互动
        self.posts = []
        self.comments = []
        self.inspirations = []  # 在睡眠期间获得的灵感
        
    def _generate_active_hours(self):
        """生成当天的随机活跃时间，避开睡眠时间"""
        # 创建所有可能的小时列表(0-23)
        all_hours = list(range(24))
        
        # 移除睡眠时间
        sleep_hours = []
        if self.sleep_start <= self.sleep_end:
            sleep_hours = list(range(self.sleep_start, self.sleep_end))
        else:  # 处理跨夜的睡眠时间（例如22点到6点）
            sleep_hours = list(range(self.sleep_start, 24)) + list(range(0, self.sleep_end))
            
        available_hours = [h for h in all_hours if h not in sleep_hours]
        
        # 确定今天该角色将活跃的小时数
        num_active_hours = random.randint(ACTIVE_HOURS_MIN, ACTIVE_HOURS_MAX)
        
        # 从可用时间中选择随机的活跃时间
        active_hours = sorted(random.sample(available_hours, min(num_active_hours, len(available_hours))))
        
        return active_hours
    
    def is_active(self, current_hour=None):
        """检查角色在当前时间是否活跃"""
        # 如果强制活跃，始终返回True
        if self.force_active:
            return True
            
        if current_hour is None:
            current_hour = datetime.datetime.now().hour
            
        return current_hour in self.active_hours
    
    def is_asleep(self, current_hour=None):
        """检查角色在当前时间是否处于睡眠状态"""
        # 如果强制活跃，始终返回False（不睡觉）
        if self.force_active:
            return False
            
        if current_hour is None:
            current_hour = datetime.datetime.now().hour
            
        if self.sleep_start <= self.sleep_end:
            return self.sleep_start <= current_hour < self.sleep_end
        else:  # 处理跨夜的睡眠时间
            return current_hour >= self.sleep_start or current_hour < self.sleep_end
    
    def set_force_active(self, state):
        """设置角色是否强制活跃"""
        self.force_active = state
        return self.force_active
    
    def create_post(self, community, prompt=None, web_search=False):
        """在社区中创建新帖子"""
        if not self.is_active() and prompt is None:
            return None  # 角色不活跃且没有手动提示
        
        # 使用角色的系统提示指导内容生成
        if prompt is None:
            # 生成一个与角色兴趣相关的主题
            topic = random.choice(self.topics_of_interest)
            prompt = f"创建一个关于{topic}的帖子，这个帖子对社区成员会有吸引力。"
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 包含相关记忆提供上下文
        context = "\n你最近的记忆和经历：\n"
        # 仅包含一部分记忆作为上下文
        for memory in self.memories[-5:]:
            context += f"- {memory}\n"
        
        # 添加背景信息（如果有）
        if self.background:
            context += f"\n你的背景：\n{self.background}\n"
            
        # 添加说话风格指导（如果有）
        if self.speaking_style:
            context += f"\n你的说话风格：\n{self.speaking_style}\n请始终保持这种风格说话。\n"
        
        messages[1]["content"] += context
        
        tools = [{
            "type": "web_search",
            "web_search": {
                "enable": web_search,
                "search_query": "" if not web_search else prompt  # 仅在启用网络搜索时设置搜索查询
            }
        }]
        
        # 调用LLM API生成帖子
        response = call_llm_api(messages, tools)
        
        # 提取生成的内容
        if response and response.choices and len(response.choices) > 0:
            post_content = response.choices[0].message.content
            
            # 在社区中创建帖子
            post_id = community.add_post(self.agent_id, self.name, post_content)
            self.posts.append(post_id)
            
            # 将此互动添加到记忆中
            self.add_memory(f"创建了一个关于{prompt.split('关于')[1] if '关于' in prompt else prompt}的帖子")
            
            return post_id
        
        return None
    
    def comment_on_post(self, community, post_id, prompt=None, web_search=False):
        """对现有帖子发表评论"""
        if not self.is_active() and prompt is None:
            return None  # 角色不活跃且没有手动提示
        
        # 获取帖子内容
        post = community.get_post(post_id)
        if not post:
            return None
        
        # 使用角色的系统提示指导评论生成
        if prompt is None:
            prompt = f"对这个帖子写一个有思考深度且简短的评论: \"{post['content']}\""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 包含相关记忆提供上下文
        context = "\n你最近的记忆和经历：\n"
        # 仅包含一部分记忆作为上下文
        for memory in self.memories[-5:]:
            context += f"- {memory}\n"
        
        # 添加背景信息（如果有）
        if self.background:
            context += f"\n你的背景：\n{self.background}\n"
            
        # 添加说话风格指导（如果有）
        if self.speaking_style:
            context += f"\n你的说话风格：\n{self.speaking_style}\n请始终保持这种风格说话。\n"
        
        messages[1]["content"] += context
        
        tools = [{
            "type": "web_search",
            "web_search": {
                "enable": web_search,
                "search_query": "" if not web_search else f"关于{post['content'][:50]}...的信息"
            }
        }]
        
        # 调用LLM API生成评论
        response = call_llm_api(messages, tools)
        
        # 提取生成的内容
        if response and response.choices and len(response.choices) > 0:
            comment_content = response.choices[0].message.content
            
            # 为帖子添加评论
            comment_id = community.add_comment(post_id, self.agent_id, self.name, comment_content)
            self.comments.append(comment_id)
            
            # 将此互动添加到记忆中
            self.add_memory(f"评论了{post['author_name']}的关于{post['content'][:30]}...的帖子")
            
            return comment_id
        
        return None
    
    def process_sleep_learning(self):
        """在睡眠时间处理记忆，生成洞察和总结"""
        if not self.is_asleep():
            return None  # 仅在睡眠时间处理
        
        # 创建一个提示来总结最近的记忆并生成洞察
        memories_text = "\n".join([f"- {memory}" for memory in self.all_memories[-20:]])  # 处理最近20条记忆
        
        prompt = f"""在你的睡眠期间，你的大脑正在处理最近的经历并生成洞察。
回顾这些最近的记忆和经历：

{memories_text}

1. 将这些经历总结为2-3个简洁、令人难忘的要点。
2. 基于这些经历生成1-2个创造性的洞察或想法。
3. 思考这些如何与你在{', '.join(self.topics_of_interest)}方面的兴趣联系起来。
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 添加背景信息和说话风格（如果有）
        if self.background:
            messages[1]["content"] += f"\n你的背景：\n{self.background}\n"
        
        # 梦境中的思考不需要强调说话风格，让思维更自由流动
        
        tools = [{
            "type": "web_search",
            "web_search": {
                "enable": False  # 睡眠处理期间不进行网络搜索
            }
        }]
        
        # 调用LLM API生成洞察
        response = call_llm_api(messages, tools)
        
        # 提取生成的内容
        if response and response.choices and len(response.choices) > 0:
            insight_content = response.choices[0].message.content
            
            # 将洞察添加到角色的灵感中
            self.inspirations.append(insight_content)
            
            # 提取关键点，作为标记为灵感的新记忆添加
            lines = insight_content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#') and len(line) > 10:
                    self.add_memory(f"[灵感] {line.strip()}")
            
            return insight_content
        
        return None
    
    def add_memory(self, memory):
        """将新记忆添加到角色的记忆库"""
        self.all_memories.append(memory)
        self.memories.append(memory)
        
        # 强制记忆限制
        while len(str(self.memories)) > 10000:  # 简化的限制检查
            self.memories.pop(0)  # 移除最旧的记忆
    
    def reset_daily_schedule(self):
        """为当天生成一组新的活跃时间"""
        self.active_hours = self._generate_active_hours()
        
    def get_status(self):
        """返回角色的当前状态"""
        current_hour = datetime.datetime.now().hour
        
        if self.force_active:
            return f"{self.name}当前处于强制活跃状态。"
        elif self.is_asleep(current_hour):
            return f"{self.name}当前正在睡觉。(睡眠时间: {self.sleep_start}-{self.sleep_end})"
        elif self.is_active(current_hour):
            return f"{self.name}当前处于活跃状态。"
        else:
            return f"{self.name}当前不在线。(今天的活跃时间: {', '.join([str(h) for h in self.active_hours])})"