import time
import random
import threading
import datetime
from utils import log_to_file, print_color

class Scheduler:
    """管理AI角色的任务调度"""
    
    def __init__(self, agents, community, memory_system, interaction_tracker):
        self.agents = agents  # {agent_id: agent_object}
        self.community = community
        self.memory_system = memory_system
        self.interaction_tracker = interaction_tracker
        self.running = False
        self.scheduler_thread = None
        
    def start(self, time_scale=60):
        """启动调度器"""
        if self.running:
            print("调度器已经在运行")
            return
            
        self.running = True
        self.time_scale = time_scale  # 每个真实分钟代表多少模拟分钟
        
        # 在单独的线程中启动调度器
        self.scheduler_thread = threading.Thread(target=self._run)
        self.scheduler_thread.daemon = True  # 设置为后台线程
        self.scheduler_thread.start()
        
        print_color("调度器已启动", "green")
        
    def stop(self):
        """停止调度器"""
        if not self.running:
            print("调度器未在运行")
            return
            
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
            
        print_color("调度器已停止", "yellow")
        
    def _run(self):
        """调度器的主循环"""
        last_hour = -1
        
        while self.running:
            current_time = datetime.datetime.now()
            current_hour = current_time.hour
            
            # 如果小时变化，重置每日计划
            if current_hour != last_hour:
                if current_hour == 0:  # 新的一天
                    self._reset_daily_schedules()
                    
                # 检查哪些角色在睡觉/醒来
                self._check_sleep_wake_transitions(current_hour)
                last_hour = current_hour
            
            # 为活跃角色调度任务
            self._schedule_active_agent_tasks(current_hour)
            
            # 等待下一个调度周期
            time.sleep(60)  # 每分钟检查一次
    
    def _reset_daily_schedules(self):
        """为所有角色重置每日计划"""
        print_color("新的一天开始，重置每日计划", "blue")
        log_to_file("重置所有角色的每日计划")
        
        for agent_id, agent in self.agents.items():
            agent.reset_daily_schedule()
            print(f"已重置 {agent.name} 的每日计划")
            # 保存状态
            self.memory_system.save_agent_state(agent)
    
    def _check_sleep_wake_transitions(self, current_hour):
        """检查哪些角色正在入睡或醒来"""
        for agent_id, agent in self.agents.items():
            # 检查是否刚开始睡觉
            if agent.sleep_start == current_hour:
                print_color(f"{agent.name} 开始睡觉", "cyan")
                log_to_file(f"{agent.name} 开始睡觉")
            
            # 检查是否刚醒来
            if agent.sleep_end == current_hour:
                print_color(f"{agent.name} 正在醒来", "cyan")
                log_to_file(f"{agent.name} 正在醒来")
                
                # 处理睡眠学习
                insights = agent.process_sleep_learning()
                if insights:
                    print(f"  {agent.name} 在睡眠期间产生了洞察")
                    log_to_file(f"{agent.name} 在睡眠期间产生了洞察: {insights[:100]}...")
    
    def _schedule_active_agent_tasks(self, current_hour):
        """为当前活跃的角色调度任务"""
        active_agents = []
        
        # 找出活跃的角色
        for agent_id, agent in self.agents.items():
            if agent.is_active(current_hour):
                active_agents.append(agent)
        
        if not active_agents:
            return  # 没有活跃的角色
            
        # 随机选择一个活跃角色执行任务
        agent = random.choice(active_agents)
        
        # 决定执行什么任务
        task_choice = random.random()
        
        if task_choice < 0.3 or not self.community.get_all_posts():  # 30%几率发帖，或者如果没有帖子
            # 创建新帖子
            self._schedule_create_post(agent)
        elif task_choice < 0.7:  # 40%几率评论
            # 评论现有帖子
            self._schedule_comment_post(agent)
        else:  # 30%几率睡眠学习（如果处于睡眠状态）
            if agent.is_asleep(current_hour):
                self._schedule_sleep_learning(agent)
    
    def _schedule_create_post(self, agent):
        """调度创建帖子的任务"""
        print_color(f"调度 {agent.name} 创建帖子", "magenta")
        
        # 随机决定是否使用网络搜索
        use_web_search = random.random() < 0.5
        
        # 创建帖子
        post_id = agent.create_post(self.community, web_search=use_web_search)
        
        if post_id:
            log_to_file(f"{agent.name} 创建了一个新帖子 (ID: {post_id})")
            
            # 保存状态
            self.memory_system.save_agent_state(agent)
    
    def _schedule_comment_post(self, agent):
        """调度评论帖子的任务"""
        # 获取最近的帖子
        posts = self.community.get_all_posts(limit=10)
        
        if not posts:
            return  # 没有可评论的帖子
        
        # 随机选择一个帖子
        post = random.choice(posts)
        
        print_color(f"调度 {agent.name} 评论 {post['author_name']} 的帖子", "magenta")
        
        # 随机决定是否使用网络搜索
        use_web_search = random.random() < 0.3
        
        # 发表评论
        comment_id = agent.comment_on_post(self.community, post['post_id'], web_search=use_web_search)
        
        if comment_id:
            log_to_file(f"{agent.name} 评论了 {post['author_name']} 的帖子 (ID: {post['post_id']})")
            
            # 记录交互
            self.interaction_tracker.record_interaction(
                agent.agent_id, 
                post['author_id'], 
                'comment',
                {'post_id': post['post_id'], 'comment_id': comment_id}
            )
            
            # 保存状态
            self.memory_system.save_agent_state(agent)
    
    def _schedule_sleep_learning(self, agent):
        """调度睡眠学习任务"""
        print_color(f"调度 {agent.name} 睡眠学习", "blue")
        
        # 处理睡眠学习
        insights = agent.process_sleep_learning()
        
        if insights:
            log_to_file(f"{agent.name} 在睡眠期间产生了洞察: {insights[:100]}...")
            
            # 保存状态
            self.memory_system.save_agent_state(agent)

    def run_forced_task(self, agent_id, task_type, **kwargs):
        """强制运行特定任务（用于测试）"""
        if agent_id not in self.agents:
            print(f"找不到ID为{agent_id}的角色")
            return None
            
        agent = self.agents[agent_id]
        
        if task_type == "create_post":
            prompt = kwargs.get("prompt")
            web_search = kwargs.get("web_search", False)
            return agent.create_post(self.community, prompt, web_search)
            
        elif task_type == "comment_post":
            post_id = kwargs.get("post_id")
            if not post_id:
                print("评论需要指定帖子ID")
                return None
                
            prompt = kwargs.get("prompt")
            web_search = kwargs.get("web_search", False)
            return agent.comment_on_post(self.community, post_id, prompt, web_search)
            
        elif task_type == "sleep_learning":
            return agent.process_sleep_learning()
            
        else:
            print(f"未知的任务类型: {task_type}")
            return None