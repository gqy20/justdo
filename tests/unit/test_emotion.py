"""单元测试：EmotionEngine 情绪价值引擎

测试 AI 驱动的情绪反馈功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from todo.emotion import EmotionEngine, EmotionScenario, trigger_emotion


class TestEmotionScenario:
    """测试 EmotionScenario 数据类"""

    def test_scenario_with_required_fields(self):
        """测试：EmotionScenario 应包含必要字段"""
        # Arrange & Act
        scenario = EmotionScenario(
            name="test_scenario",
            prompt_template="Test prompt with {var}",
            max_tokens=100,
        )

        # Assert
        assert scenario.name == "test_scenario"
        assert scenario.prompt_template == "Test prompt with {var}"
        assert scenario.max_tokens == 100
        assert scenario.temperature == 0.8  # 默认值
        assert scenario.stream is False  # 默认值
        assert scenario.fallback_messages is None  # 默认值

    def test_scenario_with_all_fields(self):
        """测试：EmotionScenario 应支持所有字段"""
        # Arrange & Act
        scenario = EmotionScenario(
            name="test",
            prompt_template="Prompt",
            max_tokens=50,
            temperature=0.5,
            stream=True,
            fallback_messages=["fallback1", "fallback2"],
        )

        # Assert
        assert scenario.stream is True
        assert scenario.temperature == 0.5
        assert scenario.fallback_messages == ["fallback1", "fallback2"]


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


class TestEmotionEngineGenerateParallel:
    """测试并行生成功能"""

    @patch.dict('os.environ', {}, clear=True)
    @pytest.mark.asyncio
    async def test_generate_parallel_calls_multiple_prompts(self):
        """测试：generate_parallel 应并行处理多个提示词"""
        # Arrange
        from todo.ai import AIConfig
        config = AIConfig(api_key="test")
        engine = EmotionEngine(config)

        mock_response1 = MagicMock()
        mock_response1.choices = [MagicMock(message=MagicMock(content="响应1"))]
        mock_response2 = MagicMock()
        mock_response2.choices = [MagicMock(message=MagicMock(content="响应2"))]

        mock_client = MagicMock()
        mock_create = MagicMock(side_effect=[mock_response1, mock_response2])
        mock_client.chat.completions.create = mock_create

        engine.client = mock_client

        # Act
        prompts = ["提示词1", "提示词2"]
        results = await engine.generate_parallel(prompts)

        # Assert
        assert len(results) == 2
        # 由于并行执行，结果的顺序可能不同
        assert set(results) == {"响应1", "响应2"}
        assert mock_create.call_count == 2


class TestTriggerEmotion:
    """测试 trigger_emotion 函数"""

    @patch('todo.emotion.EmotionEngine')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_trigger_emotion_uses_scenario_template(self, mock_engine_class):
        """测试：trigger_emotion 应使用场景模板格式化提示词"""
        # Arrange
        mock_engine = MagicMock()
        mock_engine.generate.return_value = "AI 反馈"
        mock_engine_class.return_value = mock_engine

        scenario = EmotionScenario(
            name="test",
            prompt_template="你好 {name}",
            max_tokens=50,
        )

        # Act
        result = trigger_emotion(scenario, name="用户")

        # Assert
        mock_engine.generate.assert_called_once()
        call_kwargs = mock_engine.generate.call_args.kwargs
        assert "你好 用户" in call_kwargs['prompt']
        assert call_kwargs['max_tokens'] == 50
        assert result == "AI 反馈"

    @patch('todo.emotion.EmotionEngine')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_trigger_emotion_returns_error_message_on_failure(self, mock_engine_class):
        """测试：AI 失败时应返回错误说明"""
        # Arrange
        mock_engine = MagicMock()
        mock_engine.generate.side_effect = Exception("API 错误")
        mock_engine_class.return_value = mock_engine

        scenario = EmotionScenario(
            name="test",
            prompt_template="提示词",
        )

        # Act
        result = trigger_emotion(scenario)

        # Assert - 应返回错误说明，不抛出异常
        assert "AI 暂不可用" in result
        assert "API 错误" in result
