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
    max_tokens: int = 300
    temperature: float = 0.7


class AIHandler:
    """OpenAI 处理器"""

    # 提示词模板
    PROMPT_ENHANCE = """你是任务描述优化专家。将模糊的任务描述转化为具体、可执行的行动。

需要优化的情况：
- 太模糊：看书、学习、运动 → 阅读第1章、学习Python基础、晨跑3公里
- 缺少动词：报告、会议 → 撰写报告、参加评审会议
- 没有具体内容：代码、文档 → 修复登录bug、更新API文档

优化原则：
1. 添加具体的行动动词（撰写、阅读、完成、修复）
2. 明确具体的内容或数量
3. 保持简洁（5-12字）
4. 总是尝试改进，除非原文已经很完美

原文：{text}

优化后的描述（直接输出，不要解释）："""
    PROMPT_SUGGEST = """根据待办任务列表，分析并建议下一步做哪个任务。

任务列表：
{todos}

要求：
1. 只建议一个任务
2. 分析理由（100-200字）
3. 从优先级、紧急程度、心理阻力三个维度分析
4. 输出格式：💡 建议优先完成 [任务ID]

直接输出建议："""

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
                {"role": "user", "content": self.PROMPT_ENHANCE.format(text=text)}
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

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": self.PROMPT_SUGGEST.format(todos=todos_text)}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": 0.7,
        }
        # GLM-4.x 需要禁用思考模式以加快速度
        if self._should_disable_thinking():
            params["extra_body"] = {"thinking": {"type": "disabled"}}

        response = self.client.chat.completions.create(**params)
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

    def suggest_next_stream(self, todos: List):
        """AI 建议下一步（流式输出）

        Args:
            todos: 任务列表

        Yields:
            响应文本片段
        """
        # 过滤未完成的任务
        incomplete_todos = [t for t in todos if not t.done]

        if not incomplete_todos:
            yield "🎉 所有任务已完成！"
            return

        # 格式化任务列表
        todos_text = "\n".join([
            f"- [{t.id}] {t.text} (优先级: {t.priority}, {'已完成' if t.done else '未完成'})"
            for t in incomplete_todos
        ])

        # 构建请求参数
        params = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": self.PROMPT_SUGGEST.format(todos=todos_text)}
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": 0.7,
            "stream": True,
        }
        # GLM-4.x 需要禁用思考模式以加快速度
        if self._should_disable_thinking():
            params["extra_body"] = {"thinking": {"type": "disabled"}}

        for chunk in self.client.chat.completions.create(**params):
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

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

        system_prompt = f"""你是一个友善的 Todo 助手，帮助用户管理任务和克服拖延。

当前任务列表：
{todos_text}

回答要简洁、有同理心、实用。"""

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
