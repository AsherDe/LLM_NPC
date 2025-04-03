import threading
import time
import datetime
import os
import queue
from utils import print_color

class ActivityLog:
    """活动日志管理器"""
    
    def __init__(self, max_entries=100):
        self.log_entries = []
        self.max_entries = max_entries
        self.log_queue = queue.Queue()
        self.running = False
        self.log_thread = None
    
    def start(self):
        """启动日志处理线程"""
        if self.running:
            return
            
        self.running = True
        self.log_thread = threading.Thread(target=self._process_log_entries)
        self.log_thread.daemon = True
        self.log_thread.start()
    
    def stop(self):
        """停止日志处理线程"""
        self.running = False
        if self.log_thread:
            self.log_thread.join(timeout=1)
    
    def _process_log_entries(self):
        """处理日志队列中的条目"""
        while self.running:
            try:
                # 非阻塞方式获取日志条目
                try:
                    entry = self.log_queue.get(block=False)
                    self._add_entry(entry)
                except queue.Empty:
                    pass
                    
                time.sleep(0.1)
            except Exception as e:
                print(f"日志处理错误: {e}")
    
    def _add_entry(self, entry):
        """添加日志条目到内部存储"""
        self.log_entries.append(entry)
        
        # 如果超过最大条目数，移除最旧的
        while len(self.log_entries) > self.max_entries:
            self.log_entries.pop(0)
    
    def add(self, agent_name, action_type, message, details=None):
        """添加新的日志条目"""
        timestamp = datetime.datetime.now()
        
        entry = {
            "timestamp": timestamp,
            "agent_name": agent_name,
            "action_type": action_type,
            "message": message,
            "details": details
        }
        
        # 将条目添加到队列而不是直接添加到存储
        self.log_queue.put(entry)
        
        # 同时将条目写入标准输出（可选，根据需要启用）
        self._print_entry(entry)
    
    def _print_entry(self, entry):
        """打印日志条目到标准输出"""
        timestamp_str = entry["timestamp"].strftime("%H:%M:%S")
        agent_name = entry["agent_name"]
        action_type = entry["action_type"]
        message = entry["message"]
        
        # 根据操作类型选择不同的颜色
        color = None
        if action_type == "POST":
            color = "green"
        elif action_type == "COMMENT":
            color = "blue"
        elif action_type == "SLEEP":
            color = "magenta"
        elif action_type == "WAKE":
            color = "cyan"
        elif action_type == "SYSTEM":
            color = "yellow"
        
        print_color(f"[{timestamp_str}] {agent_name} | {action_type}: {message}", color)
    
    def get_recent(self, count=10):
        """获取最近的日志条目"""
        return self.log_entries[-count:] if len(self.log_entries) > 0 else []
    
    def get_by_agent(self, agent_name, count=10):
        """获取特定角色的最近日志条目"""
        agent_entries = [entry for entry in self.log_entries if entry["agent_name"] == agent_name]
        return agent_entries[-count:] if len(agent_entries) > 0 else []
    
    def get_by_action(self, action_type, count=10):
        """获取特定操作类型的最近日志条目"""
        action_entries = [entry for entry in self.log_entries if entry["action_type"] == action_type]
        return action_entries[-count:] if len(action_entries) > 0 else []

class Monitor:
    """系统实时监控界面"""
    
    def __init__(self, agents, community, scheduler):
        self.agents = agents
        self.community = community
        self.scheduler = scheduler
        self.activity_log = ActivityLog()
        self.running = False
        self.monitor_thread = None
        
        # 添加代理钩子到调度器
        self._add_scheduler_hooks()
    
    def _add_scheduler_hooks(self):
        """为调度器添加钩子，记录系统事件"""
        # 这部分需要scheduler支持钩子，或者我们在此做适配
        # 为了简单起见，我们直接修改scheduler代码或让它调用monitor方法
        pass
    
    def log_post(self, agent_name, post_id, content_preview):
        """记录发帖活动"""
        self.activity_log.add(agent_name, "POST", content_preview, {"post_id": post_id})
    
    def log_comment(self, agent_name, post_author, post_id, comment_id, content_preview):
        """记录评论活动"""
        self.activity_log.add(
            agent_name, 
            "COMMENT", 
            f"回复 {post_author}: {content_preview}", 
            {"post_id": post_id, "comment_id": comment_id}
        )
    
    def log_sleep(self, agent_name):
        """记录角色入睡"""
        self.activity_log.add(agent_name, "SLEEP", "开始睡眠", None)
    
    def log_wake(self, agent_name, insights=None):
        """记录角色醒来"""
        if insights:
            self.activity_log.add(agent_name, "WAKE", f"醒来并获得洞察: {insights[:50]}...", None)
        else:
            self.activity_log.add(agent_name, "WAKE", "醒来", None)
    
    def log_system(self, message):
        """记录系统事件"""
        self.activity_log.add("系统", "SYSTEM", message, None)
    
    def start(self):
        """启动监控界面"""
        if self.running:
            return
            
        self.running = True
        self.activity_log.start()
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._run_monitor_interface)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.log_system("监控系统已启动")
        print_color("监控系统已启动，输入 'help' 查看可用命令", "green")
    
    def stop(self):
        """停止监控界面"""
        self.running = False
        self.activity_log.stop()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
        self.log_system("监控系统已停止")
    
    def _run_monitor_interface(self):
        """运行监控界面主循环"""
        while self.running:
            try:
                command = input("\n输入监控命令 (help 获取帮助): ").strip()
                
                if command.lower() == 'help':
                    self._show_help()
                elif command.lower() == 'status':
                    self._show_status()
                elif command.lower() == 'log':
                    self._show_log()
                elif command.lower().startswith('agent '):
                    parts = command.split(' ', 2)
                    if len(parts) >= 2:
                        self._show_agent(parts[1])
                elif command.lower() == 'posts':
                    self._show_posts()
                elif command.lower() == 'stop':
                    self._stop_scheduler()
                elif command.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                elif command.lower() == 'exit':
                    print("使用 'stop' 命令停止调度器，然后退出监控模式")
                else:
                    print_color("未知命令，输入 'help' 查看可用命令", "yellow")
            except Exception as e:
                print(f"监控界面错误: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
可用命令:
  help   - 显示此帮助信息
  status - 显示当前系统状态
  log    - 显示最近的活动日志
  agent <名称> - 显示特定角色的状态和活动
  posts  - 显示最近的帖子
  stop   - 停止调度器
  clear  - 清屏
  exit   - 退出监控模式

注意: 所有活动都会实时显示在控制台中
"""
        print(help_text)
    
    def _show_status(self):
        """显示当前系统状态"""
        current_hour = datetime.datetime.now().hour
        
        print_color(f"\n===== 系统状态 (当前时间: {current_hour}:00) =====", "cyan")
        print(f"调度器运行状态: {'运行中' if self.scheduler.running else '已停止'}")
        
        print("\n角色状态:")
        for agent_id, agent in self.agents.items():
            status = "强制活跃" if agent.force_active else (
                "活跃" if agent.is_active(current_hour) else (
                "睡眠中" if agent.is_asleep(current_hour) else "不在线"
            ))
            
            print(f"- {agent.name} ({agent.role}): {status}")
        
        post_count = len(self.community.posts)
        comment_count = len(self.community.comments)
        
        print(f"\n社区状态: {post_count}个帖子, {comment_count}条评论")
    
    def _show_log(self, count=20):
        """显示最近的活动日志"""
        entries = self.activity_log.get_recent(count)
        
        print_color(f"\n===== 最近{len(entries)}条活动 =====", "cyan")
        
        if not entries:
            print("暂无活动记录")
            return
            
        for entry in entries:
            timestamp_str = entry["timestamp"].strftime("%H:%M:%S")
            agent_name = entry["agent_name"]
            action_type = entry["action_type"]
            message = entry["message"]
            
            print(f"[{timestamp_str}] {agent_name} | {action_type}: {message}")
    
    def _show_agent(self, agent_name):
        """显示特定角色的状态和活动"""
        # 找到匹配的角色
        target_agent = None
        for agent_id, agent in self.agents.items():
            if agent.name == agent_name:
                target_agent = agent
                break
        
        if not target_agent:
            print_color(f"找不到名为 '{agent_name}' 的角色", "red")
            return
        
        print_color(f"\n===== {agent_name} ({target_agent.role}) =====", "cyan")
        
        # 显示状态
        current_hour = datetime.datetime.now().hour
        status = "强制活跃" if target_agent.force_active else (
            "活跃" if target_agent.is_active(current_hour) else (
            "睡眠中" if target_agent.is_asleep(current_hour) else "不在线"
        ))
        
        print(f"状态: {status}")
        print(f"活跃时间: {', '.join([str(h) for h in target_agent.active_hours])}")
        print(f"睡眠时间: {target_agent.sleep_start}:00 - {target_agent.sleep_end}:00")
        
        # 显示背景信息
        if hasattr(target_agent, "background") and target_agent.background:
            print("\n背景:")
            print(target_agent.background)
        
        # 显示说话风格
        if hasattr(target_agent, "speaking_style") and target_agent.speaking_style:
            print("\n说话风格:")
            print(target_agent.speaking_style)
        
        # 显示最近记忆
        print("\n最近记忆:")
        for memory in target_agent.memories[-5:]:
            print(f"- {memory}")
        
        # 显示最近活动
        entries = self.activity_log.get_by_agent(agent_name, 10)
        
        print("\n最近活动:")
        if not entries:
            print("暂无活动记录")
        else:
            for entry in entries:
                timestamp_str = entry["timestamp"].strftime("%H:%M:%S")
                action_type = entry["action_type"]
                message = entry["message"]
                
                print(f"[{timestamp_str}] {action_type}: {message}")
    
    def _show_posts(self, count=5):
        """显示最近的帖子"""
        posts = self.community.get_all_posts(limit=count)
        
        print_color(f"\n===== 最近{len(posts)}个帖子 =====", "cyan")
        
        if not posts:
            print("暂无帖子")
            return
            
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post['author_name']} 发布于 {post['timestamp'][:16]}")
            print(f"{post['content'][:200]}...")
            
            # 显示评论
            comments = self.community.get_post_comments(post['post_id'])
            if comments:
                print(f"\n  {len(comments)}条评论:")
                for j, comment in enumerate(comments[:3], 1):
                    print(f"  {j}. {comment['author_name']}: {comment['content'][:100]}...")
                
                if len(comments) > 3:
                    print(f"  ... 还有 {len(comments) - 3} 条评论")
            
            print("-" * 50)
    
    def _stop_scheduler(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.stop()
            print_color("调度器已停止", "yellow")
        else:
            print("调度器已经停止")


# 钩子函数，在主程序中与scheduler对接
def hook_monitor_to_scheduler(scheduler, monitor):
    """将监控系统与调度器对接，捕获所有活动"""
    original_schedule_create_post = scheduler._schedule_create_post
    original_schedule_comment_post = scheduler._schedule_comment_post
    original_check_sleep_wake = scheduler._check_sleep_wake_transitions
    
    # 重写发帖方法
    def new_schedule_create_post(agent):
        result = original_schedule_create_post(agent)
        # 找出最新的帖子ID并记录
        if agent.posts:
            latest_post_id = agent.posts[-1]
            post = scheduler.community.get_post(latest_post_id)
            if post:
                monitor.log_post(agent.name, latest_post_id, post['content'][:50])
        return result
    
    # 重写评论方法
    def new_schedule_comment_post(agent):
        result = original_schedule_comment_post(agent)
        # 找出最新的评论并记录
        if agent.comments:
            latest_comment_id = agent.comments[-1]
            comment = scheduler.community.comments.get(latest_comment_id)
            if comment:
                post = scheduler.community.get_post(comment['post_id'])
                if post:
                    monitor.log_comment(
                        agent.name, 
                        post['author_name'], 
                        comment['post_id'],
                        latest_comment_id,
                        comment['content'][:50]
                    )
        return result
    
    # 重写睡眠/醒来检查方法
    def new_check_sleep_wake(current_hour):
        # 先记录当前状态
        for agent_id, agent in scheduler.agents.items():
            was_asleep = agent.is_asleep(current_hour - 1 if current_hour > 0 else 23)
            is_asleep_now = agent.is_asleep(current_hour)
            
            # 检测睡眠状态变化
            if not was_asleep and is_asleep_now:
                monitor.log_sleep(agent.name)
            elif was_asleep and not is_asleep_now:
                monitor.log_wake(agent.name)
        
        # 调用原始方法
        return original_check_sleep_wake(current_hour)
    
    # 替换调度器的方法
    scheduler._schedule_create_post = new_schedule_create_post
    scheduler._schedule_comment_post = new_schedule_comment_post
    scheduler._check_sleep_wake_transitions = new_check_sleep_wake
    
    # 记录初始状态
    monitor.log_system("已将监控系统与调度器连接")
    
    return scheduler