import json
import os
import datetime
import uuid

class Community:
    def __init__(self, storage_dir="community_data"):
        self.storage_dir = storage_dir
        self.posts = {}  # post_id -> post_data
        self.comments = {}  # comment_id -> comment_data
        self.post_comments = {}  # post_id -> [comment_ids]
        
        # 如果存储目录不存在，则创建
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        # 如果有可用数据，则加载
        self.load_data()
    
    def add_post(self, author_id, author_name, content):
        """向社区添加新帖子"""
        post_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        post_data = {
            "post_id": post_id,
            "author_id": author_id,
            "author_name": author_name,
            "content": content,
            "timestamp": timestamp,
            "likes": 0
        }
        
        self.posts[post_id] = post_data
        self.post_comments[post_id] = []
        
        # 保存到磁盘
        self.save_data()
        
        # 在终端打印以便测试
        print(f"\n--- 新帖子 by {author_name} ---")
        print(content)
        print(f"--- 帖子结束 (ID: {post_id}) ---\n")
        
        return post_id
    
    def get_post(self, post_id):
        """通过ID获取帖子"""
        return self.posts.get(post_id)
    
    def get_all_posts(self, limit=None, author_id=None):
        """获取所有帖子，可选择按作者筛选"""
        posts = list(self.posts.values())
        
        if author_id:
            posts = [p for p in posts if p["author_id"] == author_id]
            
        # 按时间戳排序（最新的排在前面）
        posts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            return posts[:limit]
        return posts
    
    def add_comment(self, post_id, author_id, author_name, content):
        """为帖子添加评论"""
        if post_id not in self.posts:
            return None
            
        comment_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        comment_data = {
            "comment_id": comment_id,
            "post_id": post_id,
            "author_id": author_id,
            "author_name": author_name,
            "content": content,
            "timestamp": timestamp,
            "likes": 0
        }
        
        self.comments[comment_id] = comment_data
        self.post_comments[post_id].append(comment_id)
        
        # 保存到磁盘
        self.save_data()
        
        # 在终端打印以便测试
        post_author = self.posts[post_id]["author_name"]
        print(f"\n--- 新评论 by {author_name} 对 {post_author} 的帖子 ---")
        print(content)
        print(f"--- 评论结束 (ID: {comment_id}) ---\n")
        
        return comment_id
    
    def get_post_comments(self, post_id):
        """获取帖子的所有评论"""
        if post_id not in self.post_comments:
            return []
            
        comment_ids = self.post_comments[post_id]
        comments = [self.comments[cid] for cid in comment_ids if cid in self.comments]
        
        # 按时间戳排序（评论按最早的排在前面）
        comments.sort(key=lambda x: x["timestamp"])
        
        return comments
    
    def like_post(self, post_id):
        """为帖子添加点赞"""
        if post_id in self.posts:
            self.posts[post_id]["likes"] += 1
            self.save_data()
            return self.posts[post_id]["likes"]
        return None
    
    def like_comment(self, comment_id):
        """为评论添加点赞"""
        if comment_id in self.comments:
            self.comments[comment_id]["likes"] += 1
            self.save_data()
            return self.comments[comment_id]["likes"]
        return None
    
    def save_data(self):
        """将社区数据保存到磁盘"""
        data = {
            "posts": self.posts,
            "comments": self.comments,
            "post_comments": self.post_comments
        }
        
        filename = os.path.join(self.storage_dir, "community_data.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """从磁盘加载社区数据"""
        filename = os.path.join(self.storage_dir, "community_data.json")
        
        if not os.path.exists(filename):
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.posts = data.get("posts", {})
                self.comments = data.get("comments", {})
                self.post_comments = data.get("post_comments", {})
        except Exception as e:
            print(f"加载社区数据时出错: {e}")