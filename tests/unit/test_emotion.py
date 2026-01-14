"""单元测试：EmotionEngine 情绪价值引擎

测试 AI 驱动的情绪反馈功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from todo.emotion import EmotionEngine


class TestEmotionEngineInit:
    """测试 EmotionEngine 初始化"""

    @patch('todo.emotion.OpenAI')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_with_valid_config(self, mock_openai):
        """测试：有效配置应创建 EmotionEngine"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test-key")

        # Act
        engine = EmotionEngine(config)

        # Assert
        assert engine.config == config
        mock_openai.assert_called_once_with(api_key="test-key", base_url=None)

    @patch('todo.emotion.OpenAI')
    @patch.dict('os.environ', {'OPENAI_BASE_URL': 'https://api.test.com'})
    def test_init_with_base_url(self, mock_openai):
        """测试：应支持自定义 base_url"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test-key")

        # Act
        engine = EmotionEngine(config)

        # Assert
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.test.com"
        )


class TestEmotionEngineGenerate:
    """测试 generate 方法"""

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_calls_openai_api(self):
        """测试：generate 应调用 OpenAI API"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test")
        engine = EmotionEngine(config)

        # 直接替换整个 client，使用 Mock autospec
        mock_client = MagicMock()
        mock_create = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="AI 响应"))]
        mock_create.return_value = mock_response
        mock_client.chat.completions.create = mock_create

        engine.client = mock_client

        # Act
        result = engine.generate("测试提示词")

        # Assert
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['messages'][0]['content'] == "测试提示词"
        assert call_kwargs['max_tokens'] == 100
        assert call_kwargs['temperature'] == 0.8
        assert result == "AI 响应"

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_with_custom_params(self):
        """测试：generate 应支持自定义参数"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test")
        engine = EmotionEngine(config)

        mock_client = MagicMock()
        mock_create = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="响应"))]
        mock_create.return_value = mock_response
        mock_client.chat.completions.create = mock_create

        engine.client = mock_client

        # Act
        result = engine.generate(
            "提示词",
            max_tokens=200,
            temperature=0.5,
        )

        # Assert
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['max_tokens'] == 200
        assert call_kwargs['temperature'] == 0.5
        assert result == "响应"

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_disables_thinking_for_glm(self):
        """测试：GLM 模型应禁用思考模式"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test", model="glm-4.7")
        engine = EmotionEngine(config)

        mock_client = MagicMock()
        mock_create = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="响应"))]
        mock_create.return_value = mock_response
        mock_client.chat.completions.create = mock_create

        engine.client = mock_client

        # Act
        result = engine.generate("提示词")

        # Assert
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['extra_body'] == {"thinking": {"type": "disabled"}}
        assert result == "响应"

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_stream_mode(self):
        """测试：generate 应支持流式输出"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test")
        engine = EmotionEngine(config)

        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="你"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="好"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="！"))]),
        ]
        mock_client = MagicMock()
        mock_create = MagicMock(return_value=iter(mock_chunks))
        mock_client.chat.completions.create = mock_create

        engine.client = mock_client

        # Act
        result = "".join(engine.generate("提示词", stream=True))

        # Assert
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['stream'] is True
        assert result == "你好！"
