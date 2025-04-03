import datetime
from llm_interface import call_llm_api
from utils import summarize_text

class PostAnalyzer:
    def __init__(self):
        self.analyzed_posts = {}  # post_id -> 分析结果
    
    def analyze_post(self, post, agent):
        """分析帖子内容，提取主题、情感和兴趣点"""
        post_id = post["post_id"]
        
        # 如果已经分析过，直接返回结果
        if post_id in self.analyzed_posts:
            return self.analyzed_posts[post_id]
        
        content = post["content"]
        author_name = post["author_name"]
        
        # 构建提示
        prompt = f"""请分析以下帖子内容:

"{content}"

这个帖子是由{author_name}发布的。

请提供:
1. 主题: 这个帖子主要讨论什么话题?
2. 情感: 这个帖子的情感基调是什么(积极、消极、中性)?
3. 兴趣点: 帖子中最有趣或最重要的3个要点是什么?
4. 与你相关度: 这个帖子与你的兴趣({', '.join(agent.topics_of_interest)})的相关程度如何(高、中、低)?
5. 是否值得回复: 根据相关度和内容价值，你是否应该回复这个帖子?

请简明扼要地回答，每个部分不超过一到两句话。
"""
        
        messages = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 调用LLM API进行分析
        response = call_llm_api(messages)
        
        # 提取结果
        if response and response.choices and len(response.choices) > 0:
            analysis = response.choices[0].message.content
            
            # 缓存分析结果
            self.analyzed_posts[post_id] = {
                "post_id": post_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "analysis": analysis,
                "summary": summarize_text(content, 100)
            }
            
            return self.analyzed_posts[post_id]
        
        # 如果分析失败，返回简单的默认分析
        default_analysis = {
            "post_id": post_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "analysis": "无法分析此帖子。",
            "summary": summarize_text(content, 100)
        }
        
        self.analyzed_posts[post_id] = default_analysis
        return default_analysis
    
    def should_agent_reply(self, post, agent):
        """确定智能体是否应该回复特定帖子"""
        # 分析帖子
        analysis = self.analyze_post(post, agent)
        
        # 检查分析结果中是否明确表示应该回复
        if "是否值得回复" in analysis["analysis"] and "是" in analysis["analysis"].split("是否值得回复")[1].lower():
            return True
        
        # 如果是针对该智能体特定兴趣的帖子，增加回复可能性
        for topic in agent.topics_of_interest:
            if topic.lower() in post["content"].lower():
                return True
        
        # 默认情况下，有50%的概率回复
        import random
        return random.random() < 0.5
    
    def get_interest_level(self, post, agent):
        """评估智能体对帖子的兴趣程度 (0-10)"""
        # 分析帖子
        analysis = self.analyze_post(post, agent)
        
        # 初始兴趣值为5
        interest_level = 5
        
        # 检查相关度部分
        if "与你相关度" in analysis["analysis"]:
            relevance_text = analysis["analysis"].split("与你相关度")[1].split("\n")[0].lower()
            if "高" in relevance_text:
                interest_level += 3
            elif "中" in relevance_text:
                interest_level += 1
            elif "低" in relevance_text:
                interest_level -= 2
        
        # 检查智能体的兴趣点
        for topic in agent.topics_of_interest:
            if topic.lower() in post["content"].lower():
                interest_level += 1
                
        # 限制在0-10范围内
        return max(0, min(10, interest_level))