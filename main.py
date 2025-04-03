import time
import argparse
import datetime
from config import AI_PERSONALITIES
from env_loader import get_api_key, get_system_config, get_storage_dirs
from ai_agent import AIAgent
from memory_system import MemorySystem
from community import Community
from post_analyzer import PostAnalyzer
from interaction_tracker import InteractionTracker
from scheduler import Scheduler
from ai_behavior import AIBehaviorSystem
from monitor import Monitor, hook_monitor_to_scheduler
from utils import print_color, ensure_directory

def create_agents():
    """根据角色定义创建所有AI角色"""
    agents = {}
    
    for agent_id, personality in AI_PERSONALITIES.items():
        agent = AIAgent(
            agent_id=agent_id,
            name=personality["name"],
            role=personality["role"],
            memories=personality["memories"],
            behaviors=personality["behaviors"],
            topics_of_interest=personality["topics_of_interest"],
            system_prompt=personality["system_prompt"],
            night_owl=personality.get("night_owl", False),
            speaking_style=personality.get("speaking_style", ""),  # 添加说话风格
            background=personality.get("background", "")  # 添加背景信息
        )
        agents[agent_id] = agent
        
    return agents

def run_manual_mode(agents, community, memory_system, post_analyzer, interaction_tracker, scheduler):
    """以手动测试模式运行模拟"""
    print_color("\n===== AI社区MVP - 手动测试模式 =====\n", "cyan")
    
    while True:
        print("\n可用角色:")
        for idx, (agent_id, agent) in enumerate(agents.items(), 1):
            status = agent.get_status()
            print(f"{idx}. {agent.name} ({agent.role}) - {status}")
        
        print("\n操作:")
        print("1. 触发角色发帖")
        print("2. 触发角色评论")
        print("3. 查看所有帖子")
        print("4. 查看角色详情")
        print("5. 触发睡眠学习")
        print("6. 保存所有角色状态")
        print("7. 重置每日时间表")
        print("8. 启动自动调度器")
        print("9. 停止自动调度器")
        print("10. 分析帖子")
        print("11. 查看角色互动统计")
        print("12. 设置所有角色强制活跃状态")
        print("13. 退出")
        
        choice = input("\n输入选择 (1-13): ").strip()
        
        if choice == "1":
            # 触发角色发帖
            agent_idx = int(input("输入角色编号: ").strip()) - 1
            if agent_idx < 0 or agent_idx >= len(agents):
                print("无效的角色编号")
                continue
                
            agent_id = list(agents.keys())[agent_idx]
            agent = agents[agent_id]
            
            prompt = input("输入帖子主题 (或留空随机): ").strip()
            prompt = prompt if prompt else None
            
            web_search = input("启用网络搜索? (y/n): ").strip().lower() == 'y'
            
            post_id = agent.create_post(community, prompt, web_search)
            if post_id:
                print(f"帖子创建成功，ID: {post_id}")
            else:
                print("创建帖子失败")
                
        elif choice == "2":
            # 触发角色评论
            agent_idx = int(input("输入角色编号: ").strip()) - 1
            if agent_idx < 0 or agent_idx >= len(agents):
                print("无效的角色编号")
                continue
                
            agent_id = list(agents.keys())[agent_idx]
            agent = agents[agent_id]
            
            # 显示最近的帖子
            posts = community.get_all_posts(limit=5)
            if not posts:
                print("没有可评论的帖子")
                continue
                
            print("\n最近的帖子:")
            for idx, post in enumerate(posts, 1):
                print(f"{idx}. 作者 {post['author_name']}: {post['content'][:50]}...")
                
            post_idx = int(input("输入要评论的帖子编号: ").strip()) - 1
            if post_idx < 0 or post_idx >= len(posts):
                print("无效的帖子编号")
                continue
                
            post_id = posts[post_idx]["post_id"]
            
            prompt = input("输入评论提示 (或留空默认): ").strip()
            prompt = prompt if prompt else None
            
            web_search = input("启用网络搜索? (y/n): ").strip().lower() == 'y'
            
            comment_id = agent.comment_on_post(community, post_id, prompt, web_search)
            if comment_id:
                print(f"评论创建成功，ID: {comment_id}")
                
                # 记录互动
                post = community.get_post(post_id)
                if post:
                    interaction_tracker.record_interaction(
                        agent_id, 
                        post['author_id'], 
                        'comment',
                        {'post_id': post_id, 'comment_id': comment_id}
                    )
            else:
                print("创建评论失败")
                
        elif choice == "3":
            # 查看所有帖子
            limit = input("显示多少帖子? (默认: 10): ").strip()
            try:
                limit = int(limit) if limit else 10
            except:
                limit = 10
                
            posts = community.get_all_posts(limit=limit)
            
            print(f"\n===== 最新 {len(posts)} 帖子 =====")
            for post in posts:
                print(f"\n{post['author_name']}的帖子 发表于 {post['timestamp'][:16]}")
                print(f"点赞: {post['likes']}")
                print(f"{post['content']}")
                
                comments = community.get_post_comments(post['post_id'])
                if comments:
                    print(f"\n  {len(comments)} 条评论:")
                    for comment in comments:
                        print(f"  - {comment['author_name']}: {comment['content'][:100]}...")
                print("-" * 50)
                
        elif choice == "4":
            # 查看角色详情
            agent_idx = int(input("输入角色编号: ").strip()) - 1
            if agent_idx < 0 or agent_idx >= len(agents):
                print("无效的角色编号")
                continue
                
            agent_id = list(agents.keys())[agent_idx]
            agent = agents[agent_id]
            
            print(f"\n===== {agent.name} ({agent.role}) =====")
            print(f"状态: {agent.get_status()}")
            print(f"今日活跃时间: {', '.join([str(h) for h in agent.active_hours])}")
            print(f"睡眠时间: {agent.sleep_start}-{agent.sleep_end}")
            
            print("\n最近记忆:")
            for memory in agent.memories[-10:]:
                print(f"- {memory}")
                
            print("\n灵感:")
            for insight in agent.inspirations[-5:]:
                print(f"{insight}\n")
                
            print(f"已发布 {len(agent.posts)} 个帖子")
            print(f"已发表 {len(agent.comments)} 条评论")
            
            # 显示互动统计
            interaction_summary = interaction_tracker.get_interaction_summary(agent_id)
            print(f"\n互动统计:")
            print(f"总互动次数: {interaction_summary['total_interactions']}")
            print(f"互动角色数: {interaction_summary['unique_agents']}")
            
            if interaction_summary['total_interactions'] > 0:
                print("\n互动最多的角色:")
                for other_id, count in interaction_summary.get('most_interacted', []):
                    other_name = agents[other_id].name if other_id in agents else "未知角色"
                    print(f"- {other_name}: {count}次")
            
        elif choice == "5":
            # 触发睡眠学习
            agent_idx = int(input("输入角色编号: ").strip()) - 1
            if agent_idx < 0 or agent_idx >= len(agents):
                print("无效的角色编号")
                continue
                
            agent_id = list(agents.keys())[agent_idx]
            agent = agents[agent_id]
            
            # 为测试覆盖睡眠检查
            force = input("强制睡眠学习? (y/n): ").strip().lower() == 'y'
            
            if not force and not agent.is_asleep():
                print(f"{agent.name}没有处于睡眠状态。无法进行睡眠学习。")
                continue
            
            print(f"正在为{agent.name}处理睡眠学习...")
            insights = agent.process_sleep_learning()
            
            if insights:
                print("\n睡眠学习结果:")
                print(insights)
            else:
                print("生成洞察失败")
                
        elif choice == "6":
            # 保存所有角色状态
            for agent_id, agent in agents.items():
                memory_system.save_agent_state(agent)
            community.save_data()
            print("所有角色状态和社区数据已成功保存")
            
        elif choice == "7":
            # 重置每日时间表
            for agent_id, agent in agents.items():
                agent.reset_daily_schedule()
            print("所有角色的每日时间表已重置")
            
        elif choice == "8":
            # 启动自动调度器
            time_scale = input("每个真实分钟代表多少模拟分钟? (默认: 60): ").strip()
            try:
                time_scale = int(time_scale) if time_scale else 60
            except:
                time_scale = 60
                
            scheduler.start(time_scale)
            
        elif choice == "9":
            # 停止自动调度器
            scheduler.stop()
            
        elif choice == "10":
            # 分析帖子
            # 显示最近的帖子
            posts = community.get_all_posts(limit=5)
            if not posts:
                print("没有可分析的帖子")
                continue
                
            print("\n最近的帖子:")
            for idx, post in enumerate(posts, 1):
                print(f"{idx}. 作者 {post['author_name']}: {post['content'][:50]}...")
                
            post_idx = int(input("输入要分析的帖子编号: ").strip()) - 1
            if post_idx < 0 or post_idx >= len(posts):
                print("无效的帖子编号")
                continue
                
            post = posts[post_idx]
            
            # 选择哪个角色的视角来分析
            agent_idx = int(input("从哪个角色的视角分析? (输入角色编号): ").strip()) - 1
            if agent_idx < 0 or agent_idx >= len(agents):
                print("无效的角色编号")
                continue
                
            agent_id = list(agents.keys())[agent_idx]
            agent = agents[agent_id]
            
            print(f"\n正在从{agent.name}的视角分析帖子...")
            analysis = post_analyzer.analyze_post(post, agent)
            
            print("\n分析结果:")
            print(analysis["analysis"])
            
            interest_level = post_analyzer.get_interest_level(post, agent)
            should_reply = post_analyzer.should_agent_reply(post, agent)
            
            print(f"\n兴趣级别: {interest_level}/10")
            print(f"是否应该回复: {'是' if should_reply else '否'}")
            
        elif choice == "11":
            # 查看角色互动统计
            print("\n角色互动统计:")
            
            for agent_id, agent in agents.items():
                interaction_summary = interaction_tracker.get_interaction_summary(agent_id)
                print(f"\n{agent.name}:")
                print(f"  总互动次数: {interaction_summary['total_interactions']}")
                print(f"  互动角色数: {interaction_summary['unique_agents']}")
                
                if interaction_summary['total_interactions'] > 0:
                    print("  互动最多的角色:")
                    for other_id, count in interaction_summary.get('most_interacted', []):
                        other_name = agents[other_id].name if other_id in agents else "未知角色"
                        print(f"    - {other_name}: {count}次")
            
        elif choice == "12":
            # 设置所有角色强制活跃状态
            current_state = next(iter(agents.values())).force_active if agents else False
            new_state = not current_state
            
            state_text = "活跃" if new_state else "正常"
            confirm = input(f"确认将所有角色设置为{state_text}状态? (y/n): ").strip().lower() == 'y'
            
            if confirm:
                for agent_id, agent in agents.items():
                    agent.set_force_active(new_state)
                
                if new_state:
                    print_color("所有角色已设置为强制活跃状态，现在他们将始终保持活跃，方便测试", "green")
                    print("在这种状态下，角色将不受活跃时间和睡眠时间的限制")
                else:
                    print_color("所有角色已恢复正常状态，他们将按自己的活跃时间表行动", "yellow")
                    print(f"当前时间: {datetime.datetime.now().hour}点")
                    
                    # 显示当前时间哪些角色活跃
                    current_hour = datetime.datetime.now().hour
                    print("\n当前各角色状态:")
                    for agent_id, agent in agents.items():
                        if agent.is_active(current_hour):
                            print(f"- {agent.name}: 活跃")
                        elif agent.is_asleep(current_hour):
                            print(f"- {agent.name}: 睡眠中")
                        else:
                            print(f"- {agent.name}: 不在线")
            
        elif choice == "13":
            # 退出
            print("正在退出模拟。保存所有数据...")
            scheduler.stop()  # 确保调度器已停止
            
            for agent_id, agent in agents.items():
                memory_system.save_agent_state(agent)
            community.save_data()
            break
            
        else:
            print("无效选择。请重试。")

def main():
    parser = argparse.ArgumentParser(description='AI社区MVP模拟')
    parser.add_argument('--auto', action='store_true', help='以自动模式而非手动测试模式运行')
    parser.add_argument('--timescale', type=int, default=60, help='每个真实分钟代表多少模拟分钟')
    parser.add_argument('--monitor', action='store_true', help='启动监控界面（自动模式下默认启动）')
    args = parser.parse_args()
    
    # 获取环境变量
    api_key = get_api_key()  # 这将在config.py中设置
    storage_dirs = get_storage_dirs()
    
    # 确保存储目录存在
    for dir_path in storage_dirs.values():
        ensure_directory(dir_path)
    
    # 创建各个组件
    memory_system = MemorySystem(storage_dirs["MEMORY_STORAGE_DIR"])
    community = Community(storage_dirs["COMMUNITY_STORAGE_DIR"])
    post_analyzer = PostAnalyzer()
    interaction_tracker = InteractionTracker("interaction_data")
    behavior_system = AIBehaviorSystem()
    
    # 创建所有角色
    agents = create_agents()
    
    # 创建调度器
    scheduler = Scheduler(agents, community, memory_system, interaction_tracker, behavior_system)
    
    # 创建监控器（但不立即启动）
    monitor = Monitor(agents, community, scheduler)
    # 连接监控器与调度器
    hook_monitor_to_scheduler(scheduler, monitor)
    
    # 运行模拟
    if args.auto:
        print_color("以自动模式启动...", "green")
        
        # 在自动模式下默认启动监控界面
        if args.monitor or True:  # 总是启动监控
            monitor.start()
            
        scheduler.start(args.timescale)
        
        try:
            # 主线程不退出，让调度器和监控器在后台运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n接收到中断。正在保存数据并退出...")
            scheduler.stop()
            monitor.stop()
            
            for agent_id, agent in agents.items():
                memory_system.save_agent_state(agent)
            community.save_data()
    else:
        # 在手动模式下，可以选择是否启动监控界面
        if args.monitor:
            monitor.start()
            
        run_manual_mode(agents, community, memory_system, post_analyzer, interaction_tracker, scheduler)

if __name__ == "__main__":
    main()