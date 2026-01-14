"""OpenAI 集成模块

提供 AI 增强功能，仅依赖 OpenAI API。
"""

import os
from dataclasses import dataclass
from typing import Optional, List
from openai import OpenAI

from .prompts import (
    PROMPT_ENHANCE,
    CHAT_SYSTEM_PROMPT,
)


@dataclass
class AIConfig:
    """AI 配置"""
    api_key: str
    model: str = "gpt-4o-mini"
    max_tokens: int = 300
    temperature: float = 0.7


class AIHandler:
    """OpenAI 处理器"""

    def __init__(self, config: Optional[AIConfig] = None):
        if config is None:
            config = AIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            )
        if not config.api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")

        self.config = config
        # 支持 OPENAI_BASE_URL 环境变量（如智谱 AI）
        base_url = os.getenv("OPENAI_BASE_URL")
        self.client = OpenAI(api_key=config.api_key, base_url=base_url)

    def _should_disable_thinking(self) -> bool:
        """判断是否需要禁用思考模式（GLM-4.x 系列）"""
        return self.config.model.startswith("glm-4")

    def enhance_input(self, text: str) -> str:
        """AI 优化任务描述

        Args:
            text: 原始任务文本

        Returns:
            优化后的任务描述（如果 AI 返回空则返回原始文本）
        """
        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": PROMPT_ENHANCE.format(text=text)}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        # GLM-4.x 需要禁用思考模式以加快速度
        if self._should_disable_thinking():
            params["extra_body"] = {"thinking": {"type": "disabled"}}

        response = self.client.chat.completions.create(**params)
        enhanced = response.choices[0].message.content.strip()
        # 回退机制：如果 AI 返回空字符串，使用原始文本
        return enhanced if enhanced else text

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

        # 使用 prompts.py 中的系统提示词
        system_prompt = CHAT_SYSTEM_PROMPT.format(todos=todos_text)

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 300,
            "temperature": 0.8,
        }
        # GLM-4.x 需要禁用思考模式以加快速度
        if self._should_disable_thinking():
            params["extra_body"] = {"thinking": {"type": "disabled"}}

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content.strip()

    def chat_stream(self, user_input: str, todos: List):
        """AI 对话（流式输出）

        Args:
            user_input: 用户输入
            todos: 任务列表

        Yields:
            响应文本片段
        """
        # 格式化任务列表
        todos_text = "\n".join([
            f"- [{t.id}] {t.text} (优先级: {t.priority})"
            for t in todos
        ])

        # 使用 prompts.py 中的系统提示词
        system_prompt = CHAT_SYSTEM_PROMPT.format(todos=todos_text)

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 300,
            "temperature": 0.8,
            "stream": True,
        }
        # GLM-4.x 需要禁用思考模式以加快速度
        if self._should_disable_thinking():
            params["extra_body"] = {"thinking": {"type": "disabled"}}

        for chunk in self.client.chat.completions.create(**params):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


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
