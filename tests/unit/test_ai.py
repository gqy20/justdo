"""单元测试：AI 模块

测试 OpenAI 集成功能，使用 mock 隔离外部 API 调用
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from todo.ai import AIHandler, AIConfig, get_ai_handler


class TestAIConfig:
    """测试 AI 配置"""

    def test_config_with_required_fields(self):
        """测试：AIConfig 应包含必要字段"""
        # Arrange & Act
        config = AIConfig(
            api_key="test-key",
            model="gpt-4o-mini",
            max_tokens=100
        )

        # Assert
        assert config.api_key == "test-key"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 100
        assert config.temperature == 0.7  # 默认值

    def test_config_defaults(self):
        """测试：AIConfig 应有合理默认值"""
        # Arrange & Act
        config = AIConfig(api_key="test-key")

        # Assert
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 300
        assert config.temperature == 0.7


class TestAIHandlerInit:
    """测试 AIHandler 初始化"""

    @patch('todo.ai.OpenAI')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_with_valid_config(self, mock_openai):
        """测试：有效配置应创建 AIHandler"""
        # Arrange
        config = AIConfig(api_key="test-key")

        # Act
        handler = AIHandler(config)

        # Assert
        assert handler.config == config
        mock_openai.assert_called_once_with(api_key="test-key", base_url=None)

    def test_init_without_api_key_raises_error(self):
        """测试：缺少 API key 应抛出 ValueError"""
        # Arrange
        with patch.dict('os.environ', {}, clear=True):
            # Act & Assert
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                get_ai_handler()

    @patch('todo.ai.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key', 'OPENAI_MODEL': 'gpt-4o'})
    def test_init_from_env(self, mock_openai):
        """测试：应从环境变量读取配置"""
        # Act
        handler = get_ai_handler()

        # Assert
        assert handler.config.api_key == "env-key"
        assert handler.config.model == "gpt-4o"


class TestAIHandlerEnhanceInput:
    """测试 enhance_input 方法"""

    @patch('todo.ai.OpenAI')
    def test_enhance_input_calls_openai_api(self, mock_openai):
        """测试：enhance_input 应调用 OpenAI API"""
        # Arrange
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="优化的描述"))]
        mock_client.chat.completions.create.return_value = mock_response

        config = AIConfig(api_key="test")
        handler = AIHandler(config)

        # Act
        result = handler.enhance_input("写报告")

        # Assert
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4o-mini"
        assert "写报告" in call_args[1]['messages'][0]['content']
        assert result == "优化的描述"

    @patch('todo.ai.OpenAI')
    def test_enhance_input_strips_whitespace(self, mock_openai):
        """测试：应去除返回结果的空白字符"""
        # Arrange
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="  优化的描述  "))]
        mock_client.chat.completions.create.return_value = mock_response

        config = AIConfig(api_key="test")
        handler = AIHandler(config)

        # Act
        result = handler.enhance_input("写报告")

        # Assert
        assert result == "优化的描述"


class TestAIHandlerSuggestNext:
    """测试 suggest_next 方法"""

    @patch('todo.ai.OpenAI')
    def test_suggest_next_with_empty_todos(self, mock_openai):
        """测试：空任务列表应返回完成消息"""
        # Arrange
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        config = AIConfig(api_key="test")
        handler = AIHandler(config)

        # Act
        result = handler.suggest_next([])

        # Assert
        assert result == "🎉 所有任务已完成！"
        mock_client.chat.completions.create.assert_not_called()

    @patch('todo.ai.OpenAI')
    def test_suggest_next_filters_completed_todos(self, mock_openai):
        """测试：应过滤已完成的任务"""
        # Arrange
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="建议先做任务1"))]
        mock_client.chat.completions.create.return_value = mock_response

        # 创建模拟任务
        todo1 = MagicMock(id=1, text="任务1", done=False, priority="high")
        todo2 = MagicMock(id=2, text="任务2", done=True, priority="high")

        config = AIConfig(api_key="test")
        handler = AIHandler(config)

        # Act
        result = handler.suggest_next([todo1, todo2])

        # Assert
        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][0]['content']
        assert "任务1" in prompt
        assert "任务2" not in prompt  # 已完成任务不应在提示中
        assert result == "建议先做任务1"


class TestAIHandlerChat:
    """测试 chat 方法"""

    @patch('todo.ai.OpenAI')
    def test_chat_includes_context(self, mock_openai):
        """测试：chat 应包含任务上下文"""
        # Arrange
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="从最简单的开始"))]
        mock_client.chat.completions.create.return_value = mock_response

        todo1 = MagicMock(id=1, text="任务1", done=False, priority="high")

        config = AIConfig(api_key="test")
        handler = AIHandler(config)

        # Act
        result = handler.chat("我该做什么？", [todo1])

        # Assert
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert "任务1" in messages[0]['content']
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == "我该做什么？"
        assert result == "从最简单的开始"
