"""情绪价值引擎

提供 AI 驱动的情绪反馈功能，增强用户体验
"""

import os
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from openai import OpenAI

from .prompts import (
    PROMPT_UNIFIED_ANALYSIS,
)


class EmotionEngine:
    """情绪价值 AI 引擎"""

    def __init__(self, config):
        """初始化情绪价值引擎

        Args:
            config: AIConfig 配置对象
        """
        self.config = config
        # 支持 OPENAI_BASE_URL 环境变量（如智谱 AI）
        base_url = os.getenv("OPENAI_BASE_URL")
        self.client = OpenAI(api_key=config.api_key, base_url=base_url)

    def _should_disable_thinking(self) -> bool:
        """判断是否需要禁用思考模式（GLM-4.x 系列）"""
        return self.config.model.startswith("glm-4")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.8,
        stream: bool = False,
    ):
        """生成 AI 响应

        Args:
            prompt: 提示词
            max_tokens: 最大 token 数
            temperature: 温度参数
            stream: 是否流式输出

        Returns:
            如果 stream=False，返回响应字符串
            如果 stream=True，返回生成器，逐块 yield 响应
        """
        params = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        # GLM-4.x 需要禁用思考模式以加快速度
        if self._should_disable_thinking():
            params["extra_body"] = {"thinking": {"type": "disabled"}}

        if stream:
            # 流式模式：返回生成器
            return self._generate_stream(params)
        else:
            # 非流式模式：直接返回字符串
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content.strip()

    def _generate_stream(self, params: dict):
        """内部流式生成方法

        Args:
            params: API 参数

        Yields:
            响应文本片段
        """
        for chunk in self.client.chat.completions.create(**params):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_async(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.8,
    ) -> str:
        """异步生成 AI 响应

        Args:
            prompt: 提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            响应字符串
        """
        # 在线程池中运行同步代码，确保 stream=False
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, max_tokens, temperature, stream=False)
        )
        return result

    async def generate_parallel(
        self,
        prompts: List[str],
        max_tokens: int = 100,
        temperature: float = 0.8,
    ) -> List[str]:
        """并行生成多个 AI 响应

        Args:
            prompts: 提示词列表
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            响应字符串列表
        """
        tasks = [
            self.generate_async(p, max_tokens, temperature)
            for p in prompts
        ]
        return await asyncio.gather(*tasks)


def _get_time_context() -> str:
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


# ============================================================================
# 统一分析（一次请求完成用户画像+情感反馈）
# ============================================================================

def trigger_unified_analysis(
    total_tasks: int,
    completed_tasks: int,
    completion_rate: float,
    current_streak: int,
    longest_streak: int,
    category_stats: str,
    hourly_activity: str,
    deletion_rate: float,
    recent_7d_deletions: int,
    task_text: str,
    task_priority: str,
    time_context: str,
    today_completed: int,
    today_total: int,
    remaining_count: int,
) -> Dict:
    """触发统一分析：一次请求完成用户画像和情感反馈

    Args:
        total_tasks: 总任务数
        completed_tasks: 完成任务数
        completion_rate: 完成率
        current_streak: 当前连续打卡天数
        longest_streak: 最长连续天数
        category_stats: 类别统计文本
        hourly_activity: 时段活跃度文本
        deletion_rate: 删除率
        recent_7d_deletions: 最近7天删除数
        task_text: 当前任务文本
        task_priority: 任务优先级
        time_context: 时段
        today_completed: 今日已完成数
        today_total: 今日总任务数
        remaining_count: 剩余任务数

    Returns:
        包含 user_type, strengths_weaknesses, risk_alerts, task_feedback 的字典
    """
    from justdo.ai import get_ai_handler

    # 格式化提示词
    prompt = PROMPT_UNIFIED_ANALYSIS.format(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_rate=completion_rate,
        current_streak=current_streak,
        longest_streak=longest_streak,
        category_stats=category_stats or "暂无数据",
        hourly_activity=hourly_activity or "暂无数据",
        deletion_rate=deletion_rate,
        recent_7d_deletions=recent_7d_deletions,
        task_text=task_text,
        task_priority=task_priority,
        time_context=time_context,
        today_completed=today_completed,
        today_total=today_total,
        remaining_count=remaining_count,
    )

    # 获取 AI 引擎
    ai = get_ai_handler()
    engine = EmotionEngine(ai.config)

    try:
        response = engine.generate(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
            stream=False,
        )

        # 解析 JSON 响应
        import re
        import json
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # JSON 解析失败，返回基本结构
            return {
                "user_type": {
                    "execution_pattern": "待观察",
                    "time_preference": "待观察",
                    "activity_pattern": "待观察",
                },
                "strengths_weaknesses": {
                    "strengths": ["正在积累数据"],
                    "weaknesses": [],
                    "suggestions": ["继续坚持"],
                },
                "risk_alerts": [],
                "task_feedback": response[:50] if len(response) > 50 else response,
            }
    except Exception as e:
        # AI 调用失败，返回错误说明
        return {
            "user_type": {
                "execution_pattern": "未知",
                "time_preference": "未知",
                "activity_pattern": "未知",
            },
            "strengths_weaknesses": {
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
            },
            "risk_alerts": [],
            "task_feedback": f"（AI 暂不可用：{e}）",
        }


# ============================================================================
# 流式反馈生成（用于实时显示）
# ============================================================================

def trigger_feedback_stream(
    total_tasks: int,
    completed_tasks: int,
    completion_rate: float,
    current_streak: int,
    longest_streak: int,
    category_stats: str,
    hourly_activity: str,
    deletion_rate: float,
    recent_7d_deletions: int,
    task_text: str,
    task_priority: str,
    time_context: str,
    today_completed: int,
    today_total: int,
    remaining_count: int,
):
    """流式生成任务反馈（简化版 prompt，只生成 feedback）

    Args:
        同 trigger_unified_analysis

    Yields:
        文本片段
    """
    from justdo.ai import get_ai_handler

    # 使用简化的 prompt，只关注任务反馈
    simplified_prompt = f"""你是用户贴心的任务助手，用户刚完成了一个任务。

【用户上下文】
- 刚完成的任务：{task_text}（优先级：{task_priority}）
- 当前时段：{time_context}
- 今日已完成：{today_completed}/{today_total} 个任务
- 剩余任务数：{remaining_count} 个
- 完成率：{completion_rate:.1%}
- 连续打卡：{current_streak} 天

请分析任务并生成一句简短的鼓励/反馈（20-40字）：

分析维度：
1. 任务类型识别（工作/学习/运动/生活/日常）
2. 任务重要程度（基于优先级和内容）
3. 用户完成进度（今日完成数量 vs 总数）

反馈要求：
- 语气真诚、温暖，不要过度煽情
- 工作任务：肯定专业能力和执行力
- 学习任务：赞赏求知欲和进步
- 运动/健康：赞美自律和投资自己
- 高优先级：强调成就和重要意义
- 完成数量多：赞美执行力
- 完成数量少：鼓励"小步快跑"
- 剩余任务多：避免给压力，强调"一次一个"
- 剩余任务少：营造"即将完成"的兴奋感
- 早晨/上午：强调"好的开始"
- 深夜：认可努力，也提醒休息
- 最多用 1 个 emoji，放在句末

直接输出鼓励语，不要解释："""

    # 获取 AI 引擎
    ai = get_ai_handler()
    engine = EmotionEngine(ai.config)

    try:
        # 流式生成
        for chunk in engine._generate_stream({
            "model": ai.config.model,
            "messages": [{"role": "user", "content": simplified_prompt}],
            "max_tokens": 100,
            "temperature": 0.8,
            "stream": True,
            **({"extra_body": {"thinking": {"type": "disabled"}}}
               if engine._should_disable_thinking() else {})
        }):
            if chunk:
                yield chunk
    except Exception as e:
        # AI 调用失败
        yield f"（AI 暂不可用）"


# ============================================================================
# CLI 简化反馈（直接返回反馈文本）
# ============================================================================

def trigger_cli_feedback(
    scenario: str,
    task_text: str = "",
    task_priority: str = "",
    today_completed: int = 0,
    today_total: int = 0,
    remaining_count: int = 0,
    completed_count: int = 0,
    incomplete_count: int = 0,
    high_priority_count: int = 0,
    tasks_list: str = "",
    batch_tasks: list = None,
) -> str:
    """CLI 简化反馈：直接返回反馈文本（兼容旧 trigger_emotion 接口）

    Args:
        scenario: 场景类型 (task_completed, list_cleared, suggest, etc.)
        task_text: 任务文本
        task_priority: 任务优先级
        today_completed: 今日已完成数
        today_total: 今日总任务数
        remaining_count: 剩余任务数
        completed_count: 完成数量（用于 clear）
        incomplete_count: 未完成任务数
        high_priority_count: 高优先级任务数
        tasks_list: 任务列表文本
        batch_tasks: 批量完成的任务列表 [{"text": "...", "priority": "..."}, ...]

    Returns:
        反馈文本字符串
    """
    from justdo.ai import get_ai_handler

    # 构建 prompt（根据场景）
    if scenario == "task_completed":
        # 判断是否是批量完成
        if batch_tasks and len(batch_tasks) > 1:
            # 批量完成模式
            tasks_desc = "\n".join([
                f"  - {t['text']} (优先级: {t['priority']})"
                for t in batch_tasks
            ])
            prompt = f"""用户刚刚批量完成了 {len(batch_tasks)} 个任务：

{tasks_desc}

- 总进度：已完成 {today_completed} 个任务，共 {today_total} 个任务
- 剩余任务：{remaining_count} 个

请用一句话（20-35字）给予鼓励或反馈。要求：
- 肯定用户的执行力和效率
- 简洁、积极、有温度
- 如果完成任务较多，强调"效率"和"进步"
- 最多用 1 个 emoji，放在句末"""
        else:
            # 单个任务模式
            if batch_tasks:
                task = batch_tasks[0]
                task_text = task['text']
                task_priority = task['priority']

            prompt = f"""用户刚刚完成了一个任务：
- 任务内容：{task_text}
- 优先级：{task_priority}
- 总进度：已完成 {today_completed} 个任务，共 {today_total} 个任务
- 剩余任务：{remaining_count} 个

请用一句话（15-25字）给予鼓励或反馈。要求：简洁、积极、有温度。"""

    elif scenario == "list_cleared":
        prompt = f"""用户清除了所有已完成任务，共 {completed_count} 个。

请用一句话（15-25字）给予鼓励或反馈。要求：简洁、积极、有温度。"""

    elif scenario == "suggest":
        prompt = f"""用户有 {incomplete_count} 个未完成任务，其中 {high_priority_count} 个高优先级。

任务列表：
{tasks_list}

请用 2-3 句话给出建议（50-80字）。要求：简洁、可执行、有针对性。"""

    else:
        # 默认场景
        prompt = "请用一句话（15-25字）给予鼓励。要求：简洁、积极、有温度。"

    # 获取 AI 引擎
    ai = get_ai_handler()
    engine = EmotionEngine(ai.config)

    try:
        response = engine.generate(
            prompt=prompt,
            max_tokens=100,
            temperature=0.8,
            stream=False,
        )
        # 清理响应
        return response.strip().strip('"\'')
    except Exception:
        # 失败时返回简单消息
        if scenario == "task_completed":
            return "太棒了！继续保持！"
        elif scenario == "list_cleared":
            return "已清除所有已完成任务"
        elif scenario == "suggest":
            return "建议按优先级逐一完成"
        else:
            return "继续加油！"


def trigger_cli_feedback_stream(
    incomplete_count: int,
    high_priority_count: int,
    today_completed: int,
    tasks_list: str,
):
    """CLI 流式反馈：用于 suggest 命令

    Args:
        incomplete_count: 未完成任务数
        high_priority_count: 高优先级任务数
        today_completed: 今日已完成数
        tasks_list: 任务列表文本

    Yields:
        反馈文本片段
    """
    from justdo.ai import get_ai_handler

    prompt = f"""用户有 {incomplete_count} 个未完成任务，其中 {high_priority_count} 个高优先级。

任务列表：
{tasks_list}

请用 2-3 句话给出建议（50-80字）。要求：简洁、可执行、有针对性。"""

    # 获取 AI 引擎
    ai = get_ai_handler()
    engine = EmotionEngine(ai.config)

    try:
        # 流式生成
        for chunk in engine._generate_stream({
            "model": ai.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.8,
            "stream": True,
            **({"extra_body": {"thinking": {"type": "disabled"}}}
               if engine._should_disable_thinking() else {})
        }):
            if chunk:
                yield chunk
    except Exception:
        # 失败时返回简单建议
        yield "建议按优先级逐一完成"
