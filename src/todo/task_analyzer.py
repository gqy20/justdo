"""任务分析模块

提供任务分类、情绪检测和时段感知功能
"""

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import List


class TaskCategory(Enum):
    """任务分类枚举"""
    WORK = "工作"
    STUDY = "学习"
    EXERCISE = "运动"
    LIFE = "生活"
    OTHER = "其他"


@dataclass
class EmotionResult:
    """情绪检测结果"""
    anxiety_level: float  # 焦虑水平 0-1
    keywords: List[str]  # 检测到的关键词


# 任务分类关键词映射
CATEGORY_KEYWORDS = {
    TaskCategory.WORK: [
        "会议", "开会", "报告", "邮件", "文档", "代码", "bug", "修复",
        "开发", "部署", "评审", "需求", "项目", "工作",
        "presentation", "meeting", "report", "code", "fix"
    ],
    TaskCategory.STUDY: [
        "阅读", "课程", "练习", "笔记", "学习", "复习",
        "研究", "论文", "教程", "作业", "考试",
        "read", "study", "learn", "practice", "course"
    ],
    TaskCategory.EXERCISE: [
        "跑", "健身", "运动", "瑜伽", "游泳", "骑车",
        "锻炼", "散步", "跳绳", "俯卧撑",
        "run", "gym", "workout", "exercise", "yoga", "swim"
    ],
    TaskCategory.LIFE: [
        "购物", "清洁", "做饭", "打扫", "洗衣", "缴费",
        "买", "超市", "菜", "饭", "整理",
        "shopping", "clean", "cook", "buy", "grocery"
    ],
}

# 焦虑关键词映射（权重）
# 注意：相同关键词不应重复定义，后者会覆盖前者
ANXIETY_KEYWORDS = {
    # 高焦虑词（权重 0.55）
    "必须": 0.55,
    "死定了": 0.55,
    "来不及": 0.55,
    "来不及了": 0.55,

    # 中焦虑词（权重 0.35）
    "紧急": 0.35,
    "马上": 0.35,
    "赶紧": 0.35,
    "快点": 0.35,

    # 中低焦虑词（权重 0.2）
    "没办法": 0.2,
    "崩溃": 0.2,
    "完蛋": 0.2,

    # 轻度焦虑词（权重 0.1）
    "尽快": 0.1,
    "抓紧": 0.1,
    "最好": 0.1,
    "应该": 0.1,

    # 英文焦虑词
    "deadline": 0.3,
    "urgent": 0.3,
    "emergency": 0.6,
}


def categorize_task(text: str) -> TaskCategory:
    """分类任务

    Args:
        text: 任务文本

    Returns:
        任务类别
    """
    text_lower = text.lower()

    # 按优先级检查每个类别
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return category

    return TaskCategory.OTHER


def detect_emotion(text: str) -> EmotionResult:
    """检测任务中的情绪

    Args:
        text: 任务文本

    Returns:
        情绪检测结果
    """
    anxiety_level = 0.0
    found_keywords = []

    # 按长度降序排序关键词，优先匹配长词
    sorted_keywords = sorted(
        ANXIETY_KEYWORDS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    text_lower = text.lower()
    matched_positions = []  # 记录已匹配的位置，避免重复

    for keyword, weight in sorted_keywords:
        keyword_lower = keyword.lower()
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break

            # 检查是否与已匹配的关键词重叠
            keyword_end = pos + len(keyword)
            overlaps = any(
                not (keyword_end <= existing_start or pos >= existing_end)
                for existing_start, existing_end in matched_positions
            )

            if not overlaps:
                anxiety_level += weight
                found_keywords.append(keyword)
                matched_positions.append((pos, keyword_end))

            start = pos + 1

    # 限制在 0-1 范围内
    anxiety_level = min(anxiety_level, 1.0)

    return EmotionResult(
        anxiety_level=anxiety_level,
        keywords=found_keywords
    )


def get_time_context() -> str:
    """获取当前时段

    Returns:
        时段描述
    """
    hour = datetime.now().hour

    if 6 <= hour < 9:
        return "早晨"
    elif 9 <= hour < 12:
        return "上午"
    elif 12 <= hour < 14:
        return "中午"
    elif 14 <= hour < 18:
        return "下午"
    elif 18 <= hour < 22:
        return "晚上"
    else:
        return "深夜"


class TaskAnalyzer:
    """任务分析器

    集成任务分类、情绪检测和时段感知功能
    """

    def analyze(self, task_text: str) -> dict:
        """分析任务，返回完整上下文

        Args:
            task_text: 任务文本

        Returns:
            包含 category, emotion, time_context 的字典
        """
        return {
            "category": categorize_task(task_text),
            "emotion": detect_emotion(task_text),
            "time_context": get_time_context(),
        }
