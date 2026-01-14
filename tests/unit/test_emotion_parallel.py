"""测试并行功能的真实执行效果

验证 generate_parallel 确实是并行执行而非顺序执行
"""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock
from todo.emotion import EmotionEngine


@patch.dict('os.environ', {}, clear=True)
@pytest.mark.asyncio
async def test_generate_parallel_is_really_parallel():
    """验证：generate_parallel 确实是并行执行（比顺序快）"""
    # Arrange
    from todo.ai import AIConfig
    config = AIConfig(api_key="test")
    engine = EmotionEngine(config)

    # Mock API 调用，每次调用耗时 0.1 秒
    def slow_create(**kwargs):
        time.sleep(0.1)  # 模拟网络延迟
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=f"响应: {kwargs['messages'][0]['content']}"))]
        return mock_response

    mock_client = MagicMock()
    mock_client.chat.completions.create = slow_create
    engine.client = mock_client

    # Act - 并行执行 3 个请求
    prompts = ["提示词1", "提示词2", "提示词3"]
    start = time.time()
    results = await engine.generate_parallel(prompts)
    parallel_time = time.time() - start

    # Assert - 并行执行应该远快于顺序执行
    # 顺序执行需要 ~0.3 秒 (3 * 0.1)
    # 并行执行应该 ~0.1 秒（所有请求同时进行）
    print(f"\n并行执行时间: {parallel_time:.3f}秒")
    assert len(results) == 3
    assert parallel_time < 0.25, f"并行执行太慢: {parallel_time:.3f}秒，可能不是真正的并行"


@patch.dict('os.environ', {}, clear=True)
def test_sequential_execution_is_slower():
    """对比：顺序执行确实比并行慢"""
    from todo.ai import AIConfig
    from todo.emotion import EmotionEngine

    config = AIConfig(api_key="test")
    engine = EmotionEngine(config)

    # Mock API 调用，每次调用耗时 0.1 秒
    def slow_create(**kwargs):
        time.sleep(0.1)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="响应"))]
        return mock_response

    mock_client = MagicMock()
    mock_client.chat.completions.create = slow_create
    engine.client = mock_client

    # Act - 顺序执行 3 个请求（同步方式）
    prompts = ["提示词1", "提示词2", "提示词3"]
    start = time.time()
    results = [engine.generate(p, stream=False) for p in prompts]
    sequential_time = time.time() - start

    print(f"\n顺序执行时间: {sequential_time:.3f}秒")
    assert len(results) == 3
    assert sequential_time >= 0.25, f"顺序执行太快: {sequential_time:.3f}秒"


@patch.dict('os.environ', {}, clear=True)
@pytest.mark.asyncio
async def test_parallel_vs_sequential_comparison():
    """直接对比：并行 vs 顺序"""
    from todo.ai import AIConfig
    from todo.emotion import EmotionEngine

    config = AIConfig(api_key="test")
    engine = EmotionEngine(config)

    def slow_create(**kwargs):
        time.sleep(0.05)  # 每次调用 50ms
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="响应"))]
        return mock_response

    mock_client = MagicMock()
    mock_client.chat.completions.create = slow_create
    engine.client = mock_client

    prompts = ["A", "B", "C", "D"]

    # 并行执行
    start_parallel = time.time()
    parallel_results = await engine.generate_parallel(prompts)
    parallel_time = time.time() - start_parallel

    # 顺序执行（在事件循环中模拟）
    def sequential():
        results = []
        for p in prompts:
            results.append(engine.generate(p, stream=False))
        return results

    start_sequential = time.time()
    loop = asyncio.get_event_loop()
    sequential_results = await loop.run_in_executor(None, sequential)
    sequential_time = time.time() - start_sequential

    print(f"\n=== 性能对比 ===")
    print(f"并行执行: {parallel_time:.3f}秒")
    print(f"顺序执行: {sequential_time:.3f}秒")
    print(f"加速比: {sequential_time / parallel_time:.2f}x")

    # 并行应该显著更快
    assert parallel_time < sequential_time * 0.7, "并行执行应该比顺序快至少 30%"
