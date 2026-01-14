"""用户画像模块

提供简洁的用户行为记录和分析，100天内不超过10KB
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional


class UserProfile:
    """简洁用户画像

    记录用户行为模式，为 AI 提供个性化上下文
    """

    MAX_SIZE = 10 * 1024  # 10KB
    VERSION = 1

    def __init__(self, path: str):
        """初始化用户画像

        Args:
            path: 画像文件路径
        """
        self.path = Path(path)
        self.data = self._load_or_create()

    def _load_or_create(self) -> dict:
        """加载已存在的画像或创建新的"""
        if self.path.exists():
            try:
                content = json.loads(self.path.read_text())
                # 版本检查
                if content.get('version') != self.VERSION:
                    return self._create_new()
                return content
            except (json.JSONDecodeError, KeyError):
                return self._create_new()
        return self._create_new()

    def _create_new(self) -> dict:
        """创建新画像"""
        return {
            "version": self.VERSION,
            "created_at": date.today().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "stats": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "last_completed_date": None,
            },
            "hourly_activity": [0] * 24,  # 24小时时段
            "task_categories": {},  # {"工作": {"count": 10, "completed": 8}}
            "anxiety_patterns": {
                "high_anxiety_count": 0,
                "detected_keywords": [],
            },
            "recent_7_days": {
                "tasks_completed": 0,
                "most_active_hour": None,
            },
        }

    def record_task(self, todo, action: str):
        """记录任务事件

        Args:
            todo: TodoItem 对象
            action: 动作类型 ('add', 'complete', 'delete')
        """
        if action == 'add':
            self.data['stats']['total_tasks'] += 1

        elif action == 'complete':
            self.data['stats']['completed_tasks'] += 1
            self._update_hourly_activity()
            self._update_streak()
            self._update_categories(todo, 'complete')
            self.data['recent_7_days']['tasks_completed'] += 1

        elif action == 'delete':
            self.data['stats']['total_tasks'] = max(0, self.data['stats']['total_tasks'] - 1)

        self.data['last_updated'] = datetime.now().isoformat()

    def _update_hourly_activity(self):
        """更新时段活动统计"""
        hour = datetime.now().hour
        self.data['hourly_activity'][hour] += 1

        # 更新最近7天最活跃时段
        current_max = self.data['recent_7_days']['most_active_hour']
        if current_max is None or self.data['hourly_activity'][hour] > self.data['hourly_activity'][current_max]:
            self.data['recent_7_days']['most_active_hour'] = hour

    def _update_streak(self):
        """更新连续天数"""
        today = date.today().isoformat()
        last_completed = self.data['stats']['last_completed_date']

        if last_completed == today:
            # 今天已经完成过，不重复计数
            return

        if last_completed == (date.fromisoformat(today) - __import__('datetime').timedelta(days=1)).isoformat():
            # 昨天完成了，连续天数+1
            self.data['stats']['current_streak'] += 1
        elif last_completed != today:
            # 中断了，重置为1
            self.data['stats']['current_streak'] = 1

        # 更新最长连续天数
        if self.data['stats']['current_streak'] > self.data['stats']['longest_streak']:
            self.data['stats']['longest_streak'] = self.data['stats']['current_streak']

        self.data['stats']['last_completed_date'] = today

    def _update_categories(self, todo, action: str):
        """更新任务类别统计"""
        category = self._classify_task(todo.text)

        if category not in self.data['task_categories']:
            self.data['task_categories'][category] = {
                "count": 0,
                "completed": 0,
            }

        if action == 'complete':
            self.data['task_categories'][category]['completed'] += 1

        self.data['task_categories'][category]['count'] += 1

    def _classify_task(self, text: str) -> str:
        """简单分类任务（用于统计）"""
        text_lower = text.lower()

        # 工作关键词
        work_keywords = ["会议", "报告", "文档", "代码", "bug", "修复", "邮件"]
        # 学习关键词
        study_keywords = ["学习", "阅读", "课程", "练习", "笔记"]
        # 运动关键词
        exercise_keywords = ["跑", "健身", "运动", "瑜伽", "锻炼"]

        for keyword in work_keywords:
            if keyword in text_lower:
                return "工作"

        for keyword in study_keywords:
            if keyword in text_lower:
                return "学习"

        for keyword in exercise_keywords:
            if keyword in text_lower:
                return "运动"

        return "其他"

    def get_completion_rate(self) -> float:
        """计算完成率"""
        total = self.data['stats']['total_tasks']
        completed = self.data['stats']['completed_tasks']

        if total == 0:
            return 0.0

        return completed / total

    def get_peak_hours(self, top_n: int = 3) -> List[int]:
        """获取最活跃时段

        Args:
            top_n: 返回前 N 个时段

        Returns:
            时段列表（按活跃度降序）
        """
        activity = self.data['hourly_activity']

        if sum(activity) == 0:
            return []

        # 获取活跃度最高的时段
        indexed = list(enumerate(activity))
        indexed.sort(key=lambda x: x[1], reverse=True)

        return [h for h, count in indexed[:top_n] if count > 0]

    def get_top_category(self) -> Optional[str]:
        """获取最常做的任务类别"""
        categories = self.data['task_categories']

        if not categories:
            return None

        return max(categories.items(), key=lambda x: x[1]['count'])[0]

    def get_context_for_ai(self) -> str:
        """生成给 AI 的上下文字符串

        Returns:
            格式化的用户画像信息
        """
        stats = self.data['stats']
        completion_rate = self.get_completion_rate()
        peak_hours = self.get_peak_hours(2)
        top_category = self.get_top_category()

        context_parts = []

        # 完成率
        if stats['total_tasks'] > 0:
            context_parts.append(f"历史完成率：{completion_rate:.1%}")

        # 连续天数
        if stats['current_streak'] > 0:
            context_parts.append(f"连续使用：{stats['current_streak']}天")

        # 高效时段
        if peak_hours:
            hours_str = "、".join([f"{h}点" for h in peak_hours])
            context_parts.append(f"高效时段：{hours_str}")

        # 擅长领域
        if top_category:
            context_parts.append(f"擅长领域：{top_category}")

        if not context_parts:
            return ""

        return "【用户画像】\n" + "\n".join(f"- {part}" for part in context_parts)

    def save(self):
        """保存画像到磁盘"""
        # 检查大小
        content = json.dumps(self.data, ensure_ascii=False)
        if len(content.encode('utf-8')) > self.MAX_SIZE:
            self._cleanup()

        # 写入
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding='utf-8')

    def _cleanup(self):
        """清理旧数据，保持画像简洁"""
        # 聚合任务类别（只保留统计，不保留详细信息）
        # 这里可以添加更多清理逻辑
        pass


def get_profile_path() -> str:
    """获取用户画像文件路径

    Returns:
        画像文件绝对路径
    """
    import os

    # 使用 ~/.todo/profile.json
    todo_dir = Path.home() / '.todo'
    return str(todo_dir / 'profile.json')
