"""回收站模块

管理已删除的任务，支持恢复和永久删除
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class TrashItem:
    """回收站项目"""
    id: int
    text: str
    priority: str
    category: str
    created_at: str
    deleted_at: str
    reason: str = ""
    days_in_trash: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TrashItem':
        """从字典创建"""
        return cls(**data)


class TrashManager:
    """回收站管理器"""

    MAX_SIZE = 50 * 1024  # 50KB
    MAX_ITEMS = 100  # 最多保留100条
    AUTO_DELETE_DAYS = 30  # 30天后自动删除

    def __init__(self, path: str):
        """初始化回收站管理器

        Args:
            path: 回收站文件路径
        """
        self.path = Path(path)
        self.items: List[TrashItem] = self._load_or_create()

    def _load_or_create(self) -> List[TrashItem]:
        """加载已存在的回收站或创建新的"""
        if self.path.exists():
            try:
                content = json.loads(self.path.read_text())
                return [TrashItem.from_dict(item) for item in content]
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def add(self, todo, category: str, reason: str = "") -> TrashItem:
        """添加到回收站

        Args:
            todo: TodoItem 对象
            category: 任务类别
            reason: 删除原因

        Returns:
            创建的 TrashItem
        """
        # 更新已存在项目的 days_in_trash
        self._update_days_in_trash()

        # 检查数量限制
        if len(self.items) >= self.MAX_ITEMS:
            # 删除最旧的
            self.items.pop(0)

        # 获取创建时间（从 todo 对象或使用当前时间）
        created_at = getattr(todo, 'created_at', None)
        if created_at is None:
            created_at = datetime.now().isoformat()

        item = TrashItem(
            id=todo.id,
            text=todo.text,
            priority=todo.priority,
            category=category,
            created_at=created_at,
            deleted_at=datetime.now().isoformat(),
            reason=reason,
            days_in_trash=0,
        )

        self.items.append(item)
        self.save()

        return item

    def restore(self, todo_id: int) -> Optional[Dict]:
        """恢复任务

        Args:
            todo_id: 任务 ID

        Returns:
            恢复的任务数据，如果未找到返回 None
        """
        for i, item in enumerate(self.items):
            if item.id == todo_id:
                # 从回收站移除
                restored = self.items.pop(i)
                self.save()

                return {
                    'id': restored.id,
                    'text': restored.text,
                    'priority': restored.priority,
                    'category': restored.category,
                    'created_at': restored.created_at,
                }

        return None

    def delete_permanently(self, todo_id: int) -> bool:
        """永久删除

        Args:
            todo_id: 任务 ID

        Returns:
            是否删除成功
        """
        for i, item in enumerate(self.items):
            if item.id == todo_id:
                self.items.pop(i)
                self.save()
                return True

        return False

    def clear(self) -> int:
        """清空回收站

        Returns:
            清空的项目数量
        """
        count = len(self.items)
        self.items.clear()
        self.save()
        return count

    def cleanup_old(self, days: int = None) -> int:
        """清理旧项目

        Args:
            days: 清理 N 天前的项目，默认使用 AUTO_DELETE_DAYS

        Returns:
            清理的项目数量
        """
        if days is None:
            days = self.AUTO_DELETE_DAYS

        self._update_days_in_trash()

        cutoff_count = days
        original_count = len(self.items)

        # 保留最近 N 天的项目
        self.items = [item for item in self.items if item.days_in_trash < cutoff_count]

        removed = original_count - len(self.items)
        if removed > 0:
            self.save()

        return removed

    def _update_days_in_trash(self):
        """更新所有项目的在回收站天数"""
        now = datetime.now()
        for item in self.items:
            deleted_at = datetime.fromisoformat(item.deleted_at)
            delta = now - deleted_at
            item.days_in_trash = delta.days

    def list(self, limit: int = None, category: str = None) -> List[TrashItem]:
        """列出回收站项目

        Args:
            limit: 限制返回数量
            category: 按类别过滤

        Returns:
            TrashItem 列表（按删除时间倒序）
        """
        self._update_days_in_trash()

        # 按类别过滤
        items = self.items
        if category:
            items = [item for item in items if item.category == category]

        # 按删除时间倒序
        items = sorted(items, key=lambda x: x.deleted_at, reverse=True)

        # 限制数量
        if limit:
            items = items[:limit]

        return items

    def get_statistics(self) -> Dict:
        """获取回收站统计信息

        Returns:
            统计数据字典
        """
        self._update_days_in_trash()

        total = len(self.items)

        if total == 0:
            return {
                "total_items": 0,
                "by_category": {},
                "by_priority": {},
                "avg_days_in_trash": 0,
                "will_auto_delete": 0,
            }

        # 按类别统计
        by_category = {}
        for item in self.items:
            by_category[item.category] = by_category.get(item.category, 0) + 1

        # 按优先级统计
        by_priority = {}
        for item in self.items:
            by_priority[item.priority] = by_priority.get(item.priority, 0) + 1

        # 平均在回收站天数
        avg_days = sum(item.days_in_trash for item in self.items) / total

        # 即将自动删除的数量
        will_auto_delete = sum(
            1 for item in self.items
            if item.days_in_trash >= self.AUTO_DELETE_DAYS - 7
        )

        return {
            "total_items": total,
            "by_category": by_category,
            "by_priority": by_priority,
            "avg_days_in_trash": round(avg_days, 1),
            "will_auto_delete": will_auto_delete,
        }

    def get_analysis_for_ai(self) -> str:
        """获取用于 AI 分析的文本

        Returns:
            格式化的回收站数据
        """
        self._update_days_in_trash()

        if not self.items:
            return "回收站为空"

        stats = self.get_statistics()

        lines = [
            f"回收站统计：",
            f"- 总数：{stats['total_items']} 个",
            f"- 平均在回收站：{stats['avg_days_in_trash']} 天",
            f"- 即将自动删除：{stats['will_auto_delete']} 个",
            "",
            "按类别：",
        ]

        for cat, count in stats['by_category'].items():
            cat_names = {
                "work": "工作", "study": "学习", "exercise": "运动",
                "life": "生活", "other": "其他"
            }
            lines.append(f"- {cat_names.get(cat, cat)}：{count} 个")

        # 最近删除的项目
        recent = self.list(limit=5)
        if recent:
            lines.extend([
                "",
                "最近删除：",
            ])
            for item in recent:
                lines.append(f"- {item.text} ({item.category}) - {item.days_in_trash}天前")

        return "\n".join(lines)

    def save(self):
        """保存到磁盘"""
        # 检查大小限制
        content = json.dumps([item.to_dict() for item in self.items], ensure_ascii=False)
        if len(content.encode('utf-8')) > self.MAX_SIZE:
            # 清理旧项目
            self.cleanup_old()

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding='utf-8')


def get_trash_path() -> str:
    """获取回收站文件路径

    Returns:
        回收站文件绝对路径
    """
    jd_dir = Path.home() / '.jd'
    return str(jd_dir / 'trash.json')
