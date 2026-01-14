"""用户画像模块

提供深度用户行为分析和洞察（AI 驱动）
"""

import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from .prompts import (
    PROMPT_USER_TYPE_ANALYSIS,
    PROMPT_STRENGTHS_WEAKNESSES,
    PROMPT_RISK_ALERTS,
    PROMPT_USER_SUMMARY,
)


class UserProfile:
    """深度用户画像

    记录和分析用户行为模式，为 AI 提供个性化上下文
    使用 AI 进行核心洞察分析，保留基础统计
    """

    MAX_SIZE = 10 * 1024  # 10KB
    VERSION = 3  # 升级到 AI 驱动版本

    def __init__(self, path: str):
        """初始化用户画像

        Args:
            path: 画像文件路径
        """
        self.path = Path(path)
        self.data = self._load_or_create()
        self._ai_cache = {}  # AI 分析缓存

    def _load_or_create(self) -> dict:
        """加载已存在的画像或创建新的"""
        if self.path.exists():
            try:
                content = json.loads(self.path.read_text())
                # 版本检查
                if content.get('version') != self.VERSION:
                    return self._migrate_old_profile(content)
                return content
            except (json.JSONDecodeError, KeyError):
                return self._create_new()
        return self._create_new()

    def _migrate_old_profile(self, old_content: dict) -> dict:
        """迁移旧版本画像"""
        new_profile = self._create_new()
        # 保留基本统计数据
        if 'stats' in old_content:
            new_profile['stats'].update(old_content['stats'])
        if 'hourly_activity' in old_content:
            new_profile['hourly_activity'] = old_content['hourly_activity']
        if 'categories' in old_content:
            new_profile['categories'].update(old_content['categories'])
        return new_profile

    def _create_new(self) -> dict:
        """创建新画像"""
        return {
            "version": self.VERSION,
            "created_at": date.today().isoformat(),
            "last_updated": datetime.now().isoformat(),
            # 基础统计（保留规则计算）
            "stats": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "deleted_tasks": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "last_completed_date": None,
            },
            # 时段活跃度
            "hourly_activity": [0] * 24,
            # 任务类别统计
            "categories": {
                "work": {"created": 0, "completed": 0},
                "study": {"created": 0, "completed": 0},
                "exercise": {"created": 0, "completed": 0},
                "life": {"created": 0, "completed": 0},
                "other": {"created": 0, "completed": 0},
            },
            # 删除记录
            "deletion_history": {
                "total_deleted": 0,
                "recent_deleted": [],  # 最近50条删除记录
            },
        }

    # ========================================================================
    # 数据记录方法
    # ========================================================================

    def record_task(self, todo, action: str, category: str = "other"):
        """记录任务事件

        Args:
            todo: TodoItem 对象
            action: 动作类型 ('add', 'complete', 'delete')
            category: 任务类别 ('work', 'study', 'exercise', 'life', 'other')
        """
        if action == 'add':
            self.data['stats']['total_tasks'] += 1
            self.data['categories'][category]['created'] += 1

        elif action == 'complete':
            self.data['stats']['completed_tasks'] += 1
            self._update_hourly_activity()
            self._update_streak()
            self.data['categories'][category]['completed'] += 1

        elif action == 'delete':
            self.data['stats']['deleted_tasks'] += 1

        self.data['last_updated'] = datetime.now().isoformat()
        # 清除 AI 缓存，因为数据已更新
        self._ai_cache.clear()

    def record_deletion(self, todo_text: str, category: str, reason: str = ""):
        """记录删除事件（用于分析放弃模式）

        Args:
            todo_text: 任务文本
            category: 任务类别
            reason: 删除原因（可选）
        """
        deletion_record = {
            "text": todo_text,
            "category": category,
            "reason": reason,
            "deleted_at": datetime.now().isoformat(),
        }
        history = self.data['deletion_history']['recent_deleted']
        history.append(deletion_record)
        # 只保留最近50条
        if len(history) > 50:
            history.pop(0)
        self.data['deletion_history']['total_deleted'] += 1

    def _update_hourly_activity(self):
        """更新时段活动统计"""
        hour = datetime.now().hour
        self.data['hourly_activity'][hour] += 1

    def _update_streak(self):
        """更新连续天数"""
        today = date.today().isoformat()
        last_completed = self.data['stats']['last_completed_date']

        if last_completed == today:
            return

        yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
        if last_completed == yesterday:
            self.data['stats']['current_streak'] += 1
        elif last_completed != today:
            self.data['stats']['current_streak'] = 1

        # 更新最长连续天数
        if self.data['stats']['current_streak'] > self.data['stats']['longest_streak']:
            self.data['stats']['longest_streak'] = self.data['stats']['current_streak']

        self.data['stats']['last_completed_date'] = today

    # ========================================================================
    # 基础统计方法（保留规则计算）
    # ========================================================================

    def get_completion_rate(self) -> float:
        """计算完成率"""
        total = self.data['stats']['total_tasks']
        completed = self.data['stats']['completed_tasks']

        if total == 0:
            return 0.0

        return completed / total

    def get_peak_hours(self, top_n: int = 3) -> List[int]:
        """获取最活跃时段"""
        activity = self.data['hourly_activity']

        if sum(activity) == 0:
            return []

        indexed = list(enumerate(activity))
        indexed.sort(key=lambda x: x[1], reverse=True)

        return [h for h, count in indexed[:top_n] if count > 0]

    def _get_recent_deletions_count(self, days: int = 7) -> int:
        """获取最近 N 天的删除数量"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return sum(
            1 for item in self.data['deletion_history']['recent_deleted']
            if item['deleted_at'] >= cutoff
        )

    def _get_category_stats_text(self) -> str:
        """获取类别统计文本（用于 AI 分析）"""
        lines = []
        for cat, data in self.data['categories'].items():
            if data['created'] > 0:
                rate = data['completed'] / data['created']
                lines.append(f"- {cat}: 创建{data['created']}个，完成{data['completed']}个，完成率{rate:.1%}")
        return "\n".join(lines) if lines else "暂无数据"

    def _get_hourly_activity_text(self) -> str:
        """获取时段活跃度文本（用于 AI 分析）"""
        activity = self.data['hourly_activity']
        total = sum(activity)
        if total == 0:
            return "暂无数据"

        lines = []
        for hour, count in enumerate(activity):
            if count > 0:
                pct = count / total * 100
                lines.append(f"{hour:02d}:00 - {count}次 ({pct:.1f}%)")
        return "\n".join(lines) if lines else "暂无数据"

    # ========================================================================
    # AI 驱动的深度分析方法
    # ========================================================================

    def _get_ai_handler(self):
        """获取 AI 处理器"""
        try:
            from .ai import get_ai_handler
            return get_ai_handler()
        except (ImportError, ValueError):
            return None

    def analyze_user_type(self) -> Dict[str, str]:
        """AI 分析用户类型

        Returns:
            用户类型标签字典
        """
        # 检查缓存
        if 'user_type' in self._ai_cache:
            return self._ai_cache['user_type']

        stats = self.data['stats']
        completion_rate = self.get_completion_rate()

        # 检查是否有足够数据
        if stats['total_tasks'] < 3:
            return {
                "execution_pattern": "新用户",
                "time_preference": "待观察",
                "activity_pattern": "待观察",
            }

        # 准备 AI 分析所需的文本
        category_stats = self._get_category_stats_text()
        hourly_activity = self._get_hourly_activity_text()

        recent_deletions = self.data['deletion_history']['recent_deleted'][-5:] if self.data['deletion_history']['recent_deleted'] else []
        deletion_text = "\n".join([
            f"- {item['text']} ({item['category']}) - {item['deleted_at'][:10]}"
            for item in recent_deletions
        ]) if recent_deletions else "无"

        # 尝试使用 AI 分析
        ai = self._get_ai_handler()
        if ai:
            try:
                prompt = PROMPT_USER_TYPE_ANALYSIS.format(
                    total_tasks=stats['total_tasks'],
                    completed_tasks=stats['completed_tasks'],
                    completion_rate=completion_rate,
                    current_streak=stats['current_streak'],
                    longest_streak=stats['longest_streak'],
                    category_stats=category_stats or "暂无",
                    hourly_activity=hourly_activity or "暂无",
                    recent_deletions=deletion_text or "无",
                )

                response = ai.client.chat.completions.create(
                    model=ai.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7,
                    **({"extra_body": {"thinking": {"type": "disabled"}}}
                       if ai._should_disable_thinking() else {})
                )

                import re
                json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    # 缓存结果
                    self._ai_cache['user_type'] = result
                    return result
            except Exception:
                pass  # AI 失败时回退到规则

        # 回退到简单的规则分析
        return self._fallback_user_type(completion_rate, stats)

    def _fallback_user_type(self, completion_rate: float, stats: dict) -> Dict[str, str]:
        """回退的规则型用户类型分析"""
        total = stats['total_tasks']
        activity = self.data['hourly_activity']

        # 执行模式
        if total < 5:
            execution = "新用户"
        elif completion_rate >= 0.8:
            execution = "自律达人"
        elif completion_rate >= 0.5:
            execution = "稳步推进者"
        else:
            execution = "拖延风险"

        # 时间偏好
        morning = sum(activity[i] for i in range(6, 12))
        night = sum(activity[i] for i in list(range(21, 24)) + list(range(0, 3)))
        day = sum(activity[i] for i in range(9, 18))

        if morning > night and morning > day:
            time_pref = "早起型"
        elif night > morning and night > day:
            time_pref = "夜猫子"
        elif max(morning, night, day) == 0:
            time_pref = "待观察"
        else:
            time_pref = "全天均衡"

        # 活动模式
        total_activity = sum(activity)
        if total_activity == 0:
            activity_pattern = "待观察"
        else:
            avg_per_hour = total_activity / 24
            max_hour = max(activity)
            activity_pattern = "爆发式" if max_hour > avg_per_hour * 2 else "稳定式"

        return {
            "execution_pattern": execution,
            "time_preference": time_pref,
            "activity_pattern": activity_pattern,
        }

    def analyze_strengths_and_weaknesses(self) -> Dict[str, List[str]]:
        """AI 分析优势和短板

        Returns:
            包含 strengths, weaknesses, suggestions 列表的字典
        """
        # 检查缓存
        if 'sw_analysis' in self._ai_cache:
            return self._ai_cache['sw_analysis']

        stats = self.data['stats']
        completion_rate = self.get_completion_rate()

        # 准备类别完成情况
        cat_performance = []
        for cat, data in self.data['categories'].items():
            if data['created'] > 0:
                rate = data['completed'] / data['created']
                cat_performance.append(f"- {cat}: {rate:.1%} ({data['completed']}/{data['created']})")
        category_text = "\n".join(cat_performance) if cat_performance else "暂无"

        # 删除模式
        recent_deletions = self._get_recent_deletions_count(7)
        deletion_rate = stats['deleted_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0
        deletion_pattern = f"总删除率: {deletion_rate:.1%}, 最近一周删除: {recent_deletions}个"

        # 尝试 AI 分析
        ai = self._get_ai_handler()
        if ai and stats['total_tasks'] >= 5:
            try:
                prompt = PROMPT_STRENGTHS_WEAKNESSES.format(
                    completion_rate=completion_rate,
                    current_streak=stats['current_streak'],
                    longest_streak=stats['longest_streak'],
                    category_performance=category_text,
                    deletion_pattern=deletion_pattern,
                )

                response = ai.client.chat.completions.create(
                    model=ai.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.7,
                    **({"extra_body": {"thinking": {"type": "disabled"}}}
                       if ai._should_disable_thinking() else {})
                )

                import re
                json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    self._ai_cache['sw_analysis'] = result
                    return result
            except Exception:
                pass

        # 回退到简单的规则分析
        return self._fallback_sw_analysis(completion_rate, stats)

    def _fallback_sw_analysis(self, completion_rate: float, stats: dict) -> Dict[str, List[str]]:
        """回退的规则型优势短板分析"""
        strengths = []
        weaknesses = []

        if completion_rate >= 0.8:
            strengths.append("执行力强，完成率优秀")
        elif completion_rate >= 0.5:
            strengths.append("完成率良好")

        if stats['current_streak'] >= 7:
            strengths.append(f"连续打卡{stats['current_streak']}天")

        if completion_rate < 0.5:
            weaknesses.append("完成率有待提升")

        if stats['current_streak'] >= 14:
            weaknesses.append("需要适当休息")

        return {
            "strengths": strengths if strengths else ["正在建立习惯中"],
            "weaknesses": weaknesses if weaknesses else ["暂无明显短板"],
            "suggestions": ["继续坚持"] if completion_rate >= 0.5 else ["尝试将目标拆得更小"],
        }

    def get_risk_alerts(self) -> List[Dict]:
        """AI 生成风险预警

        Returns:
            预警列表
        """
        stats = self.data['stats']

        # 计算运动完成率
        exercise = self.data['categories']['exercise']
        exercise_rate = exercise['completed'] / exercise['created'] if exercise['created'] > 0 else 1.0

        # 未完成任务数
        incomplete = stats['total_tasks'] - stats['completed_tasks']

        # 删除率
        deletion_rate = stats['deleted_tasks'] / stats['total_tasks'] if stats['total_tasks'] > 0 else 0

        # 最近一周删除
        recent_7d = self._get_recent_deletions_count(7)

        # 尝试 AI 分析
        ai = self._get_ai_handler()
        if ai and stats['total_tasks'] >= 5:
            try:
                prompt = PROMPT_RISK_ALERTS.format(
                    current_streak=stats['current_streak'],
                    incomplete_count=incomplete,
                    deletion_rate=deletion_rate,
                    exercise_rate=f"{exercise_rate:.1%}",
                    recent_7d_deletions=recent_7d,
                )

                response = ai.client.chat.completions.create(
                    model=ai.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7,
                    **({"extra_body": {"thinking": {"type": "disabled"}}}
                       if ai._should_disable_thinking() else {})
                )

                import re
                json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result.get('alerts', [])
            except Exception:
                pass

        # 回退到规则型预警
        alerts = []

        if stats['current_streak'] >= 14:
            alerts.append({
                "level": "warning",
                "type": "overwork",
                "message": f"已连续工作{stats['current_streak']}天，建议今天休息"
            })
        elif stats['current_streak'] >= 7:
            alerts.append({
                "level": "info",
                "type": "overwork",
                "message": f"已连续打卡{stats['current_streak']}天，注意劳逸结合"
            })

        if exercise['created'] >= 5 and exercise_rate < 0.3:
            alerts.append({
                "level": "info",
                "type": "health",
                "message": f"运动任务完成率仅{exercise_rate:.0%}，需要注意健康"
            })

        if incomplete > 10:
            alerts.append({
                "level": "warning",
                "type": "overwhelm",
                "message": f"有{incomplete}个未完成任务，建议清理"
            })

        if recent_7d >= 5:
            alerts.append({
                "level": "info",
                "type": "planning",
                "message": f"最近一周删除了{recent_7d}个任务，可能需要调整目标"
            })

        return alerts

    def get_user_summary(self) -> str:
        """AI 生成用户画像总结

        Returns:
            自然语言的用户画像描述
        """
        user_type = self.analyze_user_type()
        sw = self.analyze_strengths_and_weaknesses()
        alerts = self.get_risk_alerts()

        # 尝试 AI 生成总结
        ai = self._get_ai_handler()
        if ai and self.data['stats']['total_tasks'] >= 5:
            try:
                user_type_text = f"{user_type['execution_pattern']} | {user_type['time_preference']}"
                strengths_text = "; ".join(sw.get('strengths', [])[:3])
                weaknesses_text = "; ".join(sw.get('weaknesses', [])[:3])
                alerts_text = "; ".join([a['message'] for a in alerts[:2]])

                prompt = PROMPT_USER_SUMMARY.format(
                    user_type=user_type_text,
                    strengths=strengths_text or "暂无",
                    weaknesses=weaknesses_text or "暂无",
                    alerts=alerts_text or "无",
                )

                response = ai.client.chat.completions.create(
                    model=ai.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7,
                    **({"extra_body": {"thinking": {"type": "disabled"}}}
                       if ai._should_disable_thinking() else {})
                )

                return response.choices[0].message.content.strip()
            except Exception:
                pass

        # 回退到简单总结
        main_type = f"{user_type['time_preference']}{user_type['execution_pattern']}"
        parts = [f"你是**{main_type}**"]

        if sw.get('strengths'):
            parts.append("优势：" + "、".join(sw['strengths'][:2]))

        if sw.get('weaknesses'):
            parts.append("注意：" + "、".join(sw['weaknesses'][:2]))

        return " | ".join(parts)

    def get_context_for_ai(self) -> str:
        """生成给 AI 的上下文字符串

        Returns:
            格式化的用户画像信息
        """
        user_type = self.analyze_user_type()
        sw = self.analyze_strengths_and_weaknesses()
        alerts = self.get_risk_alerts()

        context_lines = []

        # 用户类型
        context_lines.append(f"用户类型：{user_type['execution_pattern']} | {user_type['time_preference']}")

        # 统计数据
        stats = self.data['stats']
        if stats['total_tasks'] > 0:
            completion_rate = self.get_completion_rate()
            context_lines.append(f"完成率：{completion_rate:.1%}")
        if stats['current_streak'] > 0:
            context_lines.append(f"连续打卡：{stats['current_streak']}天")

        # 优势和短板
        if sw.get('strengths'):
            context_lines.append(f"优势：{'; '.join(sw['strengths'][:2])}")
        if sw.get('weaknesses'):
            context_lines.append(f"短板：{'; '.join(sw['weaknesses'][:2])}")

        # 风险预警
        if alerts:
            alert_msgs = [a['message'] for a in alerts[:2]]
            context_lines.append(f"⚠️ {'; '.join(alert_msgs)}")

        return "\n".join(context_lines)

    # ========================================================================
    # 数据持久化
    # ========================================================================

    def save(self):
        """保存画像到磁盘"""
        content = json.dumps(self.data, ensure_ascii=False)
        if len(content.encode('utf-8')) > self.MAX_SIZE:
            self._cleanup()

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding='utf-8')

    def _cleanup(self):
        """清理旧数据，保持画像简洁"""
        # 只保留最近30天的删除记录
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        self.data['deletion_history']['recent_deleted'] = [
            item for item in self.data['deletion_history']['recent_deleted']
            if item['deleted_at'] >= cutoff
        ]


def get_profile_path() -> str:
    """获取用户画像文件路径

    Returns:
        画像文件绝对路径
    """
    jd_dir = Path.home() / '.jd'
    return str(jd_dir / 'profile.json')


def guess_category(text: str) -> str:
    """根据任务文本猜测类别

    Args:
        text: 任务文本

    Returns:
        类别 ('work', 'study', 'exercise', 'life', 'other')
    """
    text_lower = text.lower()

    # 关键词匹配
    exercise_keywords = ['运动', '跑步', '健身', '锻炼', '游泳', '篮球', '瑜伽', '体能']
    study_keywords = ['学习', '阅读', '课程', '英语', '代码', '算法', '文档', '论文', '教程']
    work_keywords = ['工作', '会议', '报告', '项目', '客户', '开发', '修复', '部署', '上线']

    for keyword in exercise_keywords:
        if keyword in text_lower:
            return 'exercise'

    for keyword in study_keywords:
        if keyword in text_lower:
            return 'study'

    for keyword in work_keywords:
        if keyword in text_lower:
            return 'work'

    return 'other'
