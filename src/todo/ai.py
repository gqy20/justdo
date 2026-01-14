"""OpenAI 集成模块

提供 AI 增强功能，仅依赖 OpenAI API。
"""

import os
from dataclasses import dataclass
from typing import Optional, List
from openai import OpenAI


@dataclass
class AIConfig:
    """AI 配置"""
    api_key: str
    model: str = "gpt-4o-mini"
    max_tokens: int = 100
    temperature: float = 0.7


class AIHandler:
    """OpenAI 处理器"""

    # 提示词模板
    PROMPT_ENHANCE = "优化这个 Todo 任务描述，保持简洁有力：{text}"
    PROMPT_SUGGEST = """根据以下待办任务列表，建议下一步应该做什么：
{todos}

考虑优先级、拖延时间和任务复杂度。"""

    def __init__(self, config: Optional[AIConfig] = None):
        if config is None:
            config = AIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            )
        if not config.api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")

        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def enhance_input(self, text: str) -> str:
        """AI 优化任务描述

        Args:
            text: 原始任务文本

        Returns:
            优化后的任务描述
        """
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "user", "content": self.PROMPT_ENHANCE.format(text=text)}
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content.strip()

    def suggest_next(self, todos: List) -> str:
        """AI 建议下一步

        Args:
            todos: 任务列表

        Returns:
            建议文本
        """
        # 过滤未完成的任务
        incomplete_todos = [t for t in todos if not t.done]

        if not incomplete_todos:
            return "🎉 所有任务已完成！"

        # 格式化任务列表
        todos_text = "\n".join([
            f"- [{t.id}] {t.text} (优先级: {t.priority}, {'已完成' if t.done else '未完成'})"
            for t in incomplete_todos
        ])

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "user", "content": self.PROMPT_SUGGEST.format(todos=todos_text)}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def chat(self, user_input: str, todos: List) -> str:
        """AI 对话

        Args:
            user_input: 用户输入
            todos: 任务列表

        Returns:
            AI 回复
        """
        # 格式化任务列表
        todos_text = "\n".join([
            f"- [{t.id}] {t.text} (优先级: {t.priority})"
            for t in todos
        ])

        system_prompt = f"""你是一个友善的 Todo 助手，帮助用户管理任务和克服拖延。

当前任务列表：
{todos_text}

回答要简洁、有同理心、实用。"""

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()


def get_ai_handler() -> AIHandler:
    """获取 AI 处理器实例

    从环境变量读取配置并创建处理器

    Returns:
        AIHandler 实例

    Raises:
        ValueError: 如果缺少 OPENAI_API_KEY
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 环境变量未设置")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    return AIHandler(AIConfig(api_key=api_key, model=model))
